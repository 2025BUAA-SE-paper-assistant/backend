from functools import wraps
import json

from business.utils.reply import content_error
from scripts.check import GreenCheck

def validate_content(fields):
    """
    装饰器，用于验证 request.body 中指定字段的内容是否通过 GreenCheck 检测。
    :param fields: 字符串列表，指定需要检测的字段名
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            data = json.loads(request.body)
            greencheck = GreenCheck()
            for field in fields:
                content = data.get(field)
                if content:
                    for i in range(0, len(content), 400):
                        chunk = content[i:i+400]
                        result_status, description = greencheck.check(chunk)
                        if not result_status:
                            return content_error(description)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator