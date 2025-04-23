import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from wrap.content import validate_content
from business.utils.reply import content_error
from scripts.check import GreenCheck
from business.models.remark import Remark
from business.models.paper import Paper
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



@login_required
@require_http_methods(["POST"])
@validate_content(fields=["content"])
def create_remark(request):
    user = request.user
    data = json.loads(request.body)
    paper_id = data.get("paper_id")
    content = data.get("content")
    visibility = data.get("visibility", "private")
    paragraph_id = data.get("paragraph_id")
    paper = Paper.objects.filter(paper_id=paper_id).first()
    if not paper:
        return JsonResponse({"error": "论文不存在"}, status=404)
    if not paper_id or not content:
        return JsonResponse({"error": "缺少必填字段"}, status=400)
    if visibility not in ["private", "public"]:
        return JsonResponse({"error": "可见性选项无效"}, status=400)
    try:
        paper = Paper.objects.get(paper_id=paper_id)
        remark = Remark.objects.create(
            user=user,
            paper=paper,
            content=content,
            visibility=visibility,
            paragraph_id=paragraph_id,
        )
        return JsonResponse(
            {"message": "备注创建成功", "remark_id": remark.id},
            status=201,
        )
    except Paper.DoesNotExist:
        return JsonResponse({"error": "论文未找到"}, status=404)


@login_required
@require_http_methods(["GET"])
def get_remarks(request, paper_id):
    try:
        paper = Paper.objects.get(paper_id=paper_id)
        is_private = request.GET.get("is_private", "false").lower() == "true"
        paragraph_id = request.GET.get("paragraph_id")
        page = request.GET.get("page", 1)
        page_size = request.GET.get("page_size", 10)

        if is_private:
            remarks = Remark.objects.filter(
                paper=paper, paragraph_id=paragraph_id, user=request.user.user_id
            ).order_by("-created_at")
        else:
            remarks = Remark.objects.filter(
                Q(paper=paper, paragraph_id=paragraph_id, visibility="public")
                | Q(paper=paper, paragraph_id=paragraph_id, user=request.user.user_id)
            ).order_by("-created_at")

        paginator = Paginator(remarks, page_size)
        try:
            remarks_page = paginator.page(page)
        except PageNotAnInteger:
            return JsonResponse({"error": "无效的页码"}, status=400)
        except EmptyPage:
            return JsonResponse({"error": "页码超出范围"}, status=400)

        remarks_data = [
            {
                "id": r.id,
                "content": r.content,
                "visibility": r.visibility,
                "user": r.user.username,
                "user_avatar": r.user.avatar.url,
                "paragraph_id": r.paragraph_id,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "like_count": r.like_count(),  # Call the method to get the value
                "is_liked": r.is_liked(request.user),  # Call the method to get the value
            }
            for r in remarks_page
        ]
        result = {
            "remarks": remarks_data,
            "total_pages": paginator.num_pages,
            "current_page": remarks_page.number,
            "total_remarks": paginator.count,
        }
        return JsonResponse(result, status=200)
    except Paper.DoesNotExist:
        return JsonResponse({"error": "论文未找到"}, status=404)


@login_required
@require_http_methods(["POST"])
@validate_content(fields=["content"])
def update_remark(request, remark_id):
    try:
        remark = Remark.objects.get(id=remark_id, user=request.user)
        if not remark:
            return JsonResponse({"error": "备注未找到或无权限"}, status=403)
        data = json.loads(request.body)
        content = data.get("content")
        visibility = data.get("visibility")
        if not content:
            content = remark.content
        if visibility not in ["private", "public"]:
            return JsonResponse({"error": "可见性选项无效"}, status=400)
        if not visibility:
            visibility = remark.visibility
        remark.content = content
        remark.visibility = visibility
        remark.save()
        return JsonResponse({"message": "备注更新成功"}, status=200)
    except Remark.DoesNotExist:
        return JsonResponse({"error": "备注未找到或无权限"}, status=403)


@login_required
@require_http_methods(["DELETE"])
def delete_remark(request, remark_id):
    try:
        remark = Remark.objects.get(id=remark_id)
        user = request.user
        if user != remark.user and not user.is_superuser:
            return JsonResponse({"error": "无权限删除该备注"}, status=403)
        remark.delete()

        return JsonResponse({"message": "备注删除成功"}, status=200)
    except Remark.DoesNotExist:
        return JsonResponse({"error": "备注未找到"}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def like_remark(request, remark_id):
    try:
        remark = Remark.objects.get(id=remark_id)
        if remark.is_liked(request.user):
            remark.likes.remove(request.user)
            return JsonResponse(
                {"message": "取消点赞成功", "like_count": remark.like_count()}, status=200
            )
        else:
            remark.likes.add(request.user)
            return JsonResponse(
                {"message": "点赞成功", "like_count": remark.like_count()}, status=200
            )
    except Remark.DoesNotExist:
        return JsonResponse({"error": "备注未找到"}, status=404)

