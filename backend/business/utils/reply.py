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

def content_error():
    return JsonResponse(data={"data":"内容不符合规范，请重试","code": 422}, status=422)
