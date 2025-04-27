from django.views.decorators.http import require_http_methods
from business.utils import reply
import os
from django.conf import settings
import json
import requests

@require_http_methods(["POST"])
def translate_text(request):
    # Extract the text to be translated from the request body
    data = json.loads(request.body)
    text_to_translate = data.get("source", "")
    headers = {
        'Content-Type': 'application/json'
    }
    #data部分除了query写死
    data = {
        "query": f"{text_to_translate}", # 原文
        "temperature": 0.3, # temp
        "stream": False, 
        "model_name": "chatglm3-6b", # 模型
        "prompt_name": "translator", # prompt类型
    }

    payload = json.dumps(data)
    try:
        response = requests.post(settings.CHAT_CHAT_URL, data=payload, headers=headers, stream=False)
        translated_text = ""
        # 捕获输出
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            print(decoded_line)
            if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
                continue
        # print(decoded_line)
            if decoded_line.startswith('data'):
                data = json.loads(decoded_line.replace('data: ', ''))
                translated_text += data['text']
        # Return the translated text as a JSON response
        return reply.success(
            data={"target": translated_text}, msg="翻译成功"
        )
    except Exception as e:
        print(f"Error: {e}")
        return reply.fail(
            msg="无法连接远程服务器"
        )