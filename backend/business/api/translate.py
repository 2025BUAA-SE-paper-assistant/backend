from django.views.decorators.http import require_http_methods
from business.utils import reply
import os
from django.conf import settings
import json
import requests

ai_url = os.path.join(settings.REMOTE_MODEL_BASE_PATH, "chat", "chat")

@require_http_methods(["POST"])
def translate_text(request):
    # Extract the text to be translated from the request body
    data = request.body.decode("utf-8")
    text_to_translate = data.get("source", "")
    headers = {
        'Content-Type': 'application/json'
    }
    #data部分除了query写死
    data = {
        "query": f"{text_to_translate}", # 原文
        "temperature": 0.7, # temp
        "stream": False, 
        "model_name": "chatglm3-6b", # 模型
        "prompt_name": "translator", # prompt类型
    }

    payload = json.dumps(data)

    response = requests.post(ai_url, data=payload, headers=headers, stream=False)
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
        data={"target": translated_text}, message="翻译成功"
    )