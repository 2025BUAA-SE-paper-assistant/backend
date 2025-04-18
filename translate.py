import requests
import re, json

base_url = "http://10.2.16.28:2334/chat" #ai URL
q= 'Recent Text-to-Image (T2I) generation models such as Stable Diffusion and Imagen have made significant progress in generating high-resolution images based on text descrip tions. However, many generated images still suffer from issues such as artifacts/implausibility, misalignment with text descriptions, and low aesthetic quality. Inspired by the success of Reinforcement Learning with Human Feedback (RLHF) for large language models, prior works collected human-provided scores as feedback on generated images and trained a reward model to improve the T2I generation. In this paper, we enrich the feedback signal by (i) marking image regions that are implausible or misaligned with the text, and (ii) annotating which words in the text prompt are misrepresented or missing on the image. We collect such rich human feedback on 18K generated images (RichHF 18K) and train a multimodal transformer to predict the rich feedback automatically. We show that the predicted rich human feedback can be leveraged to improve image gener ation, for example, by selecting high-quality training data to finetune and improve the generative models, or by cre ating masks with predicted heatmaps to inpaint the prob lematic regions. Notably, the improvements generalize to models (Muse) beyond those used to generate the images on which human feedback data were collected (Stable Dif fusion variants). The RichHF-18K data set will be released soon.'
headers = {
    'Content-Type': 'application/json'
}
#data部分除了query写死
data = {
    "query": f"{q}", # 原文
    "temperature": 0.7, # temp
    "stream": False, 
    "model_name": "chatglm3-6b", # 模型
    "prompt_name": "translator", # prompt类型
}

payload = json.dumps(data)

response = requests.post(f"{base_url}/chat", data=payload, headers=headers, stream=False)
ans = ""
# 捕获输出
for line in response.iter_lines():
    decoded_line = line.decode('utf-8')
    if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
        continue
# print(decoded_line)
    if decoded_line.startswith('data'):
        data = json.loads(decoded_line.replace('data: ', ''))
        ans += data['text']

print("原文: ", q)
print("译文: ", ans)
