import requests
import re, json
import pandas as pd

with open('/usr/zjq/backend/backend/scripts/paper.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 将数据转换为DataFrame以便操作
df = pd.DataFrame(data)

# 确保至少有20条记录可以抽取，否则调整抽样数量
sample_size = min(20, len(df))

# 随机抽取样本
sampled_data = df.sample(n=sample_size)

history = ""

# 打印每篇论文的标题和摘要
i = 0
for index, row in sampled_data.iterrows():
    # print("Title:", row['title'])
    # print("Abstract:", row['abstract'])
    # print("-" * 50)  # 分隔线
    i = i + 1
    history += f"Title_{i}: {row['title']}\n"

base_url = "http://10.2.16.28:2334/chat" #ai URL
q= 'Recent Text-to-Image (T2I) generation models such as Stable Diffusion and Imagen have made significant progress in generating high-resolution images based on text descrip tions. However, many generated images still suffer from issues such as artifacts/implausibility, misalignment with text descriptions, and low aesthetic quality. Inspired by the success of Reinforcement Learning with Human Feedback (RLHF) for large language models, prior works collected human-provided scores as feedback on generated images and trained a reward model to improve the T2I generation. In this paper, we enrich the feedback signal by (i) marking image regions that are implausible or misaligned with the text, and (ii) annotating which words in the text prompt are misrepresented or missing on the image. We collect such rich human feedback on 18K generated images (RichHF 18K) and train a multimodal transformer to predict the rich feedback automatically. We show that the predicted rich human feedback can be leveraged to improve image gener ation, for example, by selecting high-quality training data to finetune and improve the generative models, or by cre ating masks with predicted heatmaps to inpaint the prob lematic regions. Notably, the improvements generalize to models (Muse) beyond those used to generate the images on which human feedback data were collected (Stable Dif fusion variants). The RichHF-18K data set will be released soon.'
headers = {
    'Content-Type': 'application/json'
}
#data部分除了query写死
data = {
    "query": f"{history}", # 原文
    "temperature": 0.3, # temp
    "stream": False, 
    "model_name": "chatglm3-6b", # 模型
    "prompt_name": "research_assistant", # prompt类型
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

pattern = r"问题\d+\.\s*(.*?)？"

# 捕获所有问题的内容
questions = re.findall(pattern, ans) #生成问题list
recommend_questions = []
for i, question in enumerate(questions, 1):
    recommend_questions.append(question)
print("历史: ", history)
print("推荐: ", ans)
print("问题捕获: ", questions)
# print(type(questions), type(recommend_questions))
print("推荐问题: ", recommend_questions)