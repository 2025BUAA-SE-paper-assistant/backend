import requests
import re, json

base_url = "http://10.2.16.28:2334/chat" #ai URL
q= 'python学习'
headers = {
    'Content-Type': 'application/json'
}
#data部分除了query写死
data = {
    "query": f"{q}", # 原文
    "temperature": 0.7, # temp
    "top_k": 10,
    "stream": True, 
    "max_tokens": 2048,
    "search_engine_name": "bing",
    "model_name": "chatglm3-6b", # 模型
    "prompt_name": "search", # prompt类型，这个有没有都可以
}

payload = json.dumps(data)

response = requests.post(f"{base_url}/search_engine_chat", data=payload, headers=headers, stream=True)
# ans = ""
# # 捕获输出
# for line in response.iter_lines():
#     decoded_line = line.decode('utf-8')
#     if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
#         continue
# # print(decoded_line)
#     if decoded_line.startswith('data'):
#         data = json.loads(decoded_line.replace('data: ', ''))
#         ans += data['text']

# print("原文: ", q)
# print("译文: ", ans)


ai_reply = ""
origin_docs = []
print(response.text)
for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
            continue
        if decoded_line.startswith('data'):
            data = decoded_line.replace('data: ', '')
            data = json.loads(data)
            if "answer" in data:
                ai_reply += data["answer"]
                print(data["answer"])
            if "docs" in data:
                for doc in data["docs"]:
                    doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                    origin_docs.append(doc)

print("回复：", ai_reply)
print("docs: ", origin_docs)