"""
论文详情页相关接口
"""

import json
import logging
import random
import time
import zipfile
import os
import requests
from django.http import JsonResponse
from business.utils.deep_translate import DeepSeek
from wrap.content import validate_content
from business.utils.reply import content_error
from scripts.check import GreenCheck
from business.models import (
    User,
    Paper,
    PaperScore,
    CommentReport,
    FirstLevelComment,
    SecondLevelComment,
    Notification,
)
# from business.utils.download_paper import downloadPaper
from backend.settings import (
    BATCH_DOWNLOAD_PATH,
    BATCH_DOWNLOAD_URL,
    USER_DOCUMENTS_PATH,
    USER_DOCUMENTS_URL,
)

if not os.path.exists(BATCH_DOWNLOAD_PATH):
    os.makedirs(BATCH_DOWNLOAD_PATH)

from business.utils.activity import update_user_activity
from django.db.models import F
from django.db import transaction
# 原子事务
@transaction.atomic
def like_paper(request):
    """
    点赞/取消点赞文献
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        paper_id = data.get("paper_id")
        # user = User.objects.filter(username=username).first()
        # paper = Paper.objects.filter(paper_id=paper_id).first()
        user = User.objects.select_for_update().filter(username=username).first()
        paper = Paper.objects.select_for_update().filter(paper_id=paper_id).first()
        # 取消点赞
        if not user or not paper_id:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
        liked = user.liked_papers.filter(paper_id=paper_id).first()
        if liked:
            user.liked_papers.remove(paper)
            # paper.like_count -= 1
            Paper.objects.filter(paper_id=paper_id).update(like_count=F('like_count') - 1)
            # user.save()
            # paper.save()
            return JsonResponse({"message": "取消点赞成功", "is_success": True})
        # 点赞
        if user and paper:
            user.liked_papers.add(paper)
            # paper.like_count += 1
            Paper.objects.filter(paper_id=paper_id).update(like_count=F('like_count') + 1)
            # user.save()
            # paper.save()

            update_user_activity(user.user_id, type='like')
            return JsonResponse({'message': '点赞成功', 'is_success': True})
        else:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)


def score_paper(request):
    """
    文献评分
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        paper_id = data.get("paper_id")
        score = data.get("score")
        user = User.objects.filter(username=username).first()
        paper = Paper.objects.filter(paper_id=paper_id).first()
        paper_score = PaperScore.objects.filter(user_id=user, paper_id=paper).first()
        # 判断用户是否对该文献进行过评分
        if paper_score:
            return JsonResponse(
                {"error": "用户已对该文献进行过评分", "is_success": False}, status=400
            )
        # 判断评分是否在1到5之间，且为整数
        if not isinstance(score, int) or score < 1 or score > 10:
            return JsonResponse(
                {"error": "评分应为0到10之间的整数", "is_success": False}, status=400
            )
        # 存储评分，更新文献平均分，保留两位小数
        if user and paper:
            paper_score = PaperScore(user_id=user, paper_id=paper, score=score)
            paper_score.save()
            paper.score_count += 1
            paper.score = round(
                (paper.score * (paper.score_count - 1) + score) / paper.score_count, 2
            )
            paper.save()
            return JsonResponse({"message": "评分成功", "is_success": True})
        else:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

@transaction.atomic
def collect_paper(request):
    """
    收藏/取消收藏文献
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        paper_id = data.get("paper_id")
        # user = User.objects.filter(username=username).first()
        # paper = Paper.objects.filter(paper_id=paper_id).first()
        user = User.objects.select_for_update().filter(username=username).first()
        paper = Paper.objects.select_for_update().filter(paper_id=paper_id).first()
        if not user or not paper:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
        collected = user.collected_papers.filter(paper_id=paper_id).first()
        # 取消收藏
        if collected:
            user.collected_papers.remove(paper)
            # paper.collect_count() -= 1
            Paper.objects.filter(paper_id=paper_id).update(collect_count=F('collect_count') - 1)
            # user.save()
            # paper.save()
            return JsonResponse({"message": "取消收藏成功", "is_success": True})
        # 收藏
        if user and paper:
            user.collected_papers.add(paper)
            # paper.collect_count += 1
            Paper.objects.filter(paper_id=paper_id).update(collect_count=F('collect_count') + 1)
            # user.save()
            # paper.save()
            return JsonResponse({"message": "收藏成功", "is_success": True})
        else:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)


def report_comment(request):
    """
    举报评论
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        comment_id = data.get("comment_id")
        comment_level = data.get("comment_level")
        report = data.get("report")
        user = User.objects.filter(username=username).first()
        # 这里需要知道是一级评论还是二级评论
        comment = None
        if comment_level == 1:
            comment = FirstLevelComment.objects.filter(comment_id=comment_id).first()
        elif comment_level == 2:
            comment = SecondLevelComment.objects.filter(comment_id=comment_id).first()
        if user and comment:
            if comment_level == 1:
                report_com = CommentReport(
                    comment_id_1=comment, comment_level=1, user_id=user, content=report
                )
                report_com.save()
            elif comment_level == 2:
                report_com = CommentReport(
                    comment_id_2=comment, comment_level=2, user_id=user, content=report
                )
                report_com.save()
            return JsonResponse({"message": "举报成功", "is_success": True})
        else:
            return JsonResponse(
                {"error": "用户或评论不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

from business.utils.activity import update_user_activity
@validate_content(fields=["comment"])
def comment_paper(request):
    """
    用户评论（含一级、二级评论）
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        paper_id = data.get("paper_id")
        comment_level = data.get("comment_level")  # 1 / 2
        text = data.get("comment")
        user = User.objects.filter(username=username).first()
        paper = Paper.objects.filter(paper_id=paper_id).first()
        if user and paper:
            update_user_activity(user.user_id, type='comment')
            if comment_level == 1:
                comment = FirstLevelComment(user_id=user, paper_id=paper, text=text)
                comment.save()
            elif comment_level == 2:
                level1_comment_id = data.get("level1_comment_id")
                level1_comment = FirstLevelComment.objects.filter(
                    comment_id=level1_comment_id
                ).first()
                # 如果是回复二级评论的评论，获取其回复的二级评论的id
                reply_comment_id = data.get("reply_comment_id")
                reply_comment = None
                if reply_comment_id:
                    reply_comment = SecondLevelComment.objects.filter(
                        comment_id=reply_comment_id
                    ).first()
                comment = SecondLevelComment(
                    user_id=user,
                    paper_id=paper,
                    text=text,
                    level1_comment=level1_comment,
                    reply_comment=reply_comment,
                )
                comment.save()
            paper.comment_count += 1
            paper.save()
            return JsonResponse({"message": "评论成功", "is_success": True})
        else:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)


def get_first_comment(request):
    """
    获取一级评论
    """
    if request.method == "GET":
        username = request.session.get("username")
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse(
                {"error": "用户未登录", "is_success": False}, status=400
            )
        paper_id = request.GET.get("paper_id")
        comments = FirstLevelComment.objects.filter(paper_id=paper_id)
        data = []
        for comment in comments:
            if comment.visibility is False:
                continue
            second_len = SecondLevelComment.objects.filter(
                level1_comment_id=comment.comment_id
            ).count()
            data.append(
                {
                    "comment_id": comment.comment_id,
                    "date": comment.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "text": comment.text,
                    "like_count": comment.like_count(),
                    "username": comment.user_id.username,
                    "user_image": comment.user_id.avatar.url,
                    "user_liked": comment.liked_by_users.filter(username=user).first()
                    is not None,
                    "second_len": second_len,
                }
            )
        total = len(data)
        return JsonResponse(
            {
                "message": "获取成功",
                "total": total,
                "comments": data,
                "is_success": True,
            }
        )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)


def get_second_comment(request):
    """
    获取二级评论
    """
    if request.method == "GET":
        username = request.session.get("username")
        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse(
                {"error": "用户未登录", "is_success": False}, status=400
            )
        level1_comment_id = request.GET.get("comment1_id")
        comments = SecondLevelComment.objects.filter(
            level1_comment_id=level1_comment_id
        )
        data = []
        for comment in comments:
            if comment.level1_comment.visibility is False:
                continue
            if comment.reply_comment and comment.reply_comment.visibility is False:
                continue
            if comment.visibility is False:
                continue
            data.append(
                {
                    "comment_id": comment.comment_id,
                    "date": comment.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "text": comment.text,
                    "like_count": comment.like_count(),
                    "to_username": (
                        comment.reply_comment.user_id.username
                        if comment.reply_comment
                        else None
                    ),
                    "username": comment.user_id.username,
                    "user_image": comment.user_id.avatar.url,
                    "user_liked": comment.liked_by_users.filter(username=user).first()
                    is not None,
                }
            )
        return JsonResponse(
            {"message": "获取成功", "comments": data, "is_success": True}
        )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

from business.utils.activity import update_user_activity
def like_comment(request):
    """
    点赞评论/取消点赞评论
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        comment_id = data.get("comment_id")
        comment_level = data.get("comment_level")
        user = User.objects.filter(username=username).first()
        # 这里需要知道是一级评论还是二级评论
        comment = None
        if comment_level == 1:
            comment = FirstLevelComment.objects.filter(comment_id=comment_id).first()
        elif comment_level == 2:
            comment = SecondLevelComment.objects.filter(comment_id=comment_id).first()
        if user and comment:
            liked = comment.liked_by_users.filter(user_id=user.user_id).first()
            update_user_activity(user.user_id, type='like')
            # 取消点赞
            if liked:
                # comment.like_count -= 1
                comment.liked_by_users.remove(user)
                comment.save()
                return JsonResponse({"message": "取消点赞成功", "is_success": True})
            # 点赞
            else:
                # comment.like_count += 1
                comment.liked_by_users.add(user)
                comment.save()
                # 被点赞的评论的作者收到通知
                notification = Notification(user_id=comment.user_id, title="你被赞了！")
                paper = comment.paper_id
                paper_title = paper.title
                notification.content = (
                    "你在论文《"
                    + paper_title
                    + "》的评论被用户"
                    + user.username
                    + "点赞了！"
                )
                notification.save()
                return JsonResponse({"message": "点赞成功", "is_success": True})
        else:
            return JsonResponse(
                {"error": "用户或评论不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

from business.api.paper_interpret import get_paper_local_url
def batch_download_papers(request):
    """
    批量下载文献
    """
    if request.method == "POST":
        data = json.loads(request.body)
        username = request.session.get("username")
        paper_ids = data.get("paper_id_list")
        user = User.objects.filter(username=username).first()
        papers = Paper.objects.filter(paper_id__in=paper_ids)
        if user and papers:
            for paper in papers:
                local_url = get_paper_local_url(paper)
                # 首先判断文献是否有本地副本，没有则下载到服务器
                # if not paper.local_path or not os.path.exists(paper.local_path):
                #     original_url = paper.original_url
                #     # 将路径中的abs修改为pdf，最后加上.pdf后缀
                #     original_url = original_url.replace("abs", "pdf") + ".pdf"
                #     # 访问url，下载文献到服务器
                #     filename = str(paper.paper_id)
                #     local_path = downloadPaper(original_url, filename)
                #     paper.local_path = local_path
                #     paper.save()

            # 确保BATCH_DOWNLOAD_PATH目录存在
            os.makedirs(BATCH_DOWNLOAD_PATH, exist_ok=True)

            # 确保ZIP文件所在目录存在
            zip_name = (
                username
                + "_batchDownload_"
                + time.strftime("%Y%m%d%H%M%S")
                + "_%d" % random.randint(0, 100)
                + ".zip"
            )
            zip_file_path = os.path.join(BATCH_DOWNLOAD_PATH, zip_name)
            os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)

            valid_papers = [p for p in papers if os.path.exists(p.local_path)]
            if not valid_papers:
                return JsonResponse(
                    {"error": "没有可下载的文件", "is_success": False}, status=400
                )

            # 将所有paper打包成zip文件
            with zipfile.ZipFile(zip_file_path, "w") as z:
                for paper in valid_papers:
                    z.write(paper.local_path, paper.title + ".pdf")
            zip_url = BATCH_DOWNLOAD_URL + zip_name
            return JsonResponse(
                {"message": "下载成功", "zip_url": zip_url, "is_success": True}
            )
        else:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)
import tqdm
def refrech_abstract_cn(request):
    """
    刷新文献的中文摘要
    """
    max_retries = 3
    if request.method == "POST":
        papers = Paper.objects.all()
        for paper in tqdm.tqdm(papers):
            if not paper.abstract_cn:
                # abstract_cn = DeepSeek().translate_text(paper.abstract)
                attempt = 1
                while attempt <= max_retries:
                    try:
                        abstract_cn = translate(paper.abstract)
                        paper.abstract_cn = abstract_cn
                        paper.save()
                        break
                    except Exception as e:
                        if attempt == max_retries:
                            logging.error(f"翻译失败: {e}-{paper.paper_id}")
                            break
                        attempt += 1

        return JsonResponse({"message": "刷新成功", "is_success": True})
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

from business.api.translate import translate, translate_argos
def get_paper_info(request):
    """
    获取文献信息
    """
    if request.method == "GET":
        paper_id = request.GET.get("paper_id")
        paper = Paper.objects.filter(paper_id=paper_id).first()
        if paper:
            bibtex = "none"
            if not paper.abstract_cn:
                # abstract_cn = DeepSeek().translate_text(paper.abstract)
                abstract_cn = translate(paper.abstract)
                paper.abstract_cn = abstract_cn
                paper.save()
            if not paper.title_cn:
                # title_cn = translate(paper.title)
                title_cn = translate_argos(paper.title)
                paper.title_cn = title_cn
                paper.save()
            if not paper.bibtex:
                bibtex = paper.original_url.replace("abs", "bibtex")
                response = requests.get(bibtex, timeout=10)
                if response.status_code == 200:
                    bibtex = response.text.strip()
                paper.bibtex = bibtex
                paper.save()


            response = {
                "message": "获取成功",
                "paper_id": paper.paper_id,
                "title": paper.title,
                'title_cn':paper.title_cn,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "abstract_cn": paper.abstract_cn,
                "publication_date": paper.publication_date.strftime("%Y-%m-%d"),
                "journal": paper.journal,
                "citation_count": paper.citation_count,
                "read_count": paper.read_count,
                "like_count": paper.like_count if paper.like_count else paper.get_like_count(),
                "collect_count": paper.collect_count if paper.collect_count else paper.get_collect_count(),
                "download_count": paper.download_count,
                "comment_count": paper.comment_count,
                "score": paper.score,
                "score_count": paper.score_count,
                "original_url": paper.original_url,
                "bibtex": paper.bibtex,
                "is_success": True,
                "paragraph": paper.paragraph,
                "mind_map":paper.get_mind_map(),
            }
            return JsonResponse(response, status=200)
        else:
            return JsonResponse(
                {"error": "文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

def get_user_paper_info(request):
    """
    获得用户对论文的收藏、点赞、评分情况
    """
    if request.method == "GET":
        username = request.session.get("username")
        paper_id = request.GET.get("paper_id")
        user = User.objects.filter(username=username).first()
        paper = Paper.objects.filter(paper_id=paper_id).first()
        if user and paper:
            liked = user.liked_papers.filter(paper_id=paper_id).first()
            collected = user.collected_papers.filter(paper_id=paper_id).first()
            scored = PaperScore.objects.filter(user_id=user, paper_id=paper).first()
            return JsonResponse(
                {
                    "message": "获取成功",
                    "liked": True if liked else False,
                    "collected": True if collected else False,
                    "scored": True if scored else False,
                    "score": scored.score if scored else 0,
                    "is_success": True,
                }
            )
        else:
            return JsonResponse(
                {"error": "用户或文献不存在", "is_success": False}, status=400
            )
    else:
        return JsonResponse({"error": "请求方法错误", "is_success": False}, status=400)

from django.views.decorators.http import require_http_methods
import re
# def extract_title(text):
#     pattern = r'^\s*(?:<(?:翻译|答案|回答)>(?P<title1>.+?)</(?:翻译|答案|回答)>|【(?P<title2>.+?)】|\"(?P<title3>.+?)\"|(?P<title4>.+?))\n'
#     match = re.match(pattern, text)
#     if match:
#         # 检查各个捕获组，返回第一个匹配到的标题
#         for group in ['title1', 'title2', 'title3', 'title4']:
#             if match.group(group):
#                 return match.group(group).strip()
    # return None  # 如果没有匹配到标题，返回 None
# def extract_title(text):
#     # 提取第一行内容
#     first_line_match = re.search(r'^.*?(?=\n|$)', text)
#     if not first_line_match:
#         return ''
#     first_line = first_line_match.group().strip()

#     # 尝试匹配被包裹的标题
#     title_match = re.fullmatch(
#         r'\s*(?:<[^>]+>|【[^】]*】|["“])\s*(.*?)\s*(?:<\/[^>]+>|】|["”])\s*',
#         first_line
#     )
#     if title_match and title_match.group(1).strip():
#         return title_match.group(1).strip()
#     else:
#         return first_line
def contains_chinese(text):
    """检查字符串中是否包含至少一个中文字符"""
    pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')  # 覆盖基本和扩展中文字符范围
    return bool(pattern.search(text))
@require_http_methods(["POST"])
def check_all_title_cn(request):
    papers = Paper.objects.all()
    bad_papers = []
    max_retries = 3
    for paper in tqdm.tqdm(papers):
        if not paper.title_cn or not contains_chinese(paper.title_cn):
            attempt = 1
            while attempt <= max_retries:
                try:
                    # sub_text = paper.title.split(':',1)
                    # # print(sub_text)
                    # if len(sub_text) == 1:
                    #     title_cn = translate_argos(paper.title)
                    # else:
                    #     # A:B
                    #     title_cn = sub_text[0] + ': ' +translate_argos(sub_text[1])
                    # print(title_cn)
                    title_cn = translate_argos(paper.title)
                    paper.title_cn = title_cn
                    paper.save()
                    break
                except Exception as e:
                    attempt += 1
                    if attempt > max_retries:
                        print(f"Failed to translate {paper.title} for exception{e}")
                        bad_papers.append(paper.title)
    return JsonResponse({"bad_papers": bad_papers},status=200)

@require_http_methods(['POST'])
def check_all_bibtex(request):
    papers = Paper.objects.all()
    max_retries = 3
    bad_papers = []
    for paper in tqdm.tqdm(papers):
        if not paper.bibtex:
            attempt = 1
            while attempt <= max_retries:
                try:
                    bibtex = paper.original_url.replace('abs','bibtex')
                    response = requests.get(bibtex, timeout=10)
                    if response.status_code == 200:
                        bibtex = response.text.strip()
                    else:
                        raise Exception('Failed to get bibtex')
                    paper.bibtex = bibtex
                    paper.save()
                    break
                except Exception as e:
                    attempt += 1
                    if attempt > max_retries:
                        print(f"Failed to get bibtex {paper.title}")
                        bad_papers.append(paper.title)
    return JsonResponse({"bad_papers": bad_papers},status=200)


