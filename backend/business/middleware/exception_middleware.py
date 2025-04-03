import logging
from django.http import JsonResponse


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def __call__(self, request):
        try:
            self.logger.info(
                f"{request.user}-访问通过{request.method}请求访问接口{request.path}"
            )
            response = self.get_response(request)
            self.logger.info(f"用户访问接口的结果: {response.status_code},返回值为: {response.content}")
        except Exception as e:
            self.logger.error(
                f"{request.user}-访问通过{request.method}请求访问接口{request.path}时发生错误: {str(e)}"
            )
            return JsonResponse({"error": str(e)}, status=500)
        return response
