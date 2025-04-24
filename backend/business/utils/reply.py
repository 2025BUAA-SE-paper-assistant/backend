from django.http import JsonResponse


def success(data=None, msg: str = ''):
    if data is None:
        data = dict()
    data['message'] = msg
    return JsonResponse(data=data, status=200)


def fail(data: dict = None, msg: str = ''):
    if data is None:
        data = dict()
    data['message'] = msg
    return JsonResponse(data=data, status=400)

def content_error(description: str = ''):
    """
    内容不符合规范
    :param description: 描述
    :return:
    """
    return JsonResponse(data={"message": description if description else "内容不符合规范，请重试", "is_success": False}, status=200)
