from django.views.decorators.http import require_http_methods
from business.utils import reply
import os
from django.conf import settings
import json
import requests

def translate_libre(src):
    api_url = 'https://libretranslate.com/translate'
    headers = {
        'Content-Type': 'application/json'
    }
    body = {
        'q':src,
        'source':'en',
        'target':'zh-Hans',
    }
    response = requests.post(api_url, data=json.dumps(body), headers=headers)
    print(response.json())
    dst = response.json()['translatedText']
    return dst

import argostranslate.package
import argostranslate.translate


def argos_init():
    from_code = "en"
    to_code = "zh"
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    matching_packages = list(filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    ))

    if not matching_packages:
        raise ValueError(f"No translation package found for {from_code}->{to_code}")
    
    package_to_install = matching_packages[0]
    argostranslate.package.install_from_path(package_to_install.download())

def translate_argos(src):
    from_code = "en"
    to_code = "zh"
    return argostranslate.translate.translate(src, from_code, to_code)


def translate(src):
    headers = {
        'Content-Type': 'application/json'
    }
    #data部分除了query写死
    data = {
        "query": f"{src}", # 原文
        "temperature": 0.3, # temp
        "stream": False, 
        "model_name": "chatglm3-6b", # 模型
        "prompt_name": "translator", # prompt类型
    }

    payload = json.dumps(data)
    response = requests.post(settings.CHAT_CHAT_URL, data=payload, headers=headers, stream=False)
    dst = ""
    # 捕获输出
    for line in response.iter_lines():
        decoded_line = line.decode('utf-8')
        # print(decoded_line)
        if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
            continue
    # print(decoded_line)
        if decoded_line.startswith('data'):
            data = json.loads(decoded_line.replace('data: ', ''))
            dst += data['text']
    # Return the translated text as a JSON response
    return dst


@require_http_methods(["POST"])
def translate_text(request):
    # Extract the text to be translated from the request body
    data = json.loads(request.body)
    text_to_translate = data.get("source", "")
    
    try:
        translated_text = translate(text_to_translate)
        return reply.success(
            data={"target": translated_text}, msg="翻译成功"
        )
    except Exception as e:
        print(f"Error: {e}")
        return reply.fail(
            msg="无法连接远程服务器"
        )
if __name__ == '__main__':
    # argos_init()
    print(translate_argos('MiniGPT-4: Enhancing Vision-Language Understanding with Advanced Large Language Models'))
