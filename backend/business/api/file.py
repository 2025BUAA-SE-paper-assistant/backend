from django.http import FileResponse, JsonResponse, HttpResponse
import os

from backend.settings import MEDIA_URL, MEDIA_ROOT, BASE_DIR


def return_file(request,file_path):
    try:
        path = request.path
        # 检查文件是否存在
        if path.startswith(MEDIA_URL):
            relative_path = path.replace(MEDIA_URL, '', 1)
            path = os.path.join(MEDIA_ROOT, relative_path)
        if os.path.exists(path):
            # 打开文件
            file = open(path, 'rb')  # 不使用 with，确保文件在响应期间保持打开
            response = FileResponse(file)
            return response
        else:
            return HttpResponse('文件不存在', status=404)
    except Exception as e:
        return HttpResponse(f'发生错误: {str(e)}', status=500)