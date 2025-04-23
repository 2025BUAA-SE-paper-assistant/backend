import requests
import re, json

base_url = "http://10.2.16.28:2334/chat"
# q= 'Recent Text-to-Image (T2I) generation models such as Stable Diffusion and Imagen have made significant progress in generating high-resolution images based on text descrip tions. However, many generated images still suffer from issues such as artifacts/implausibility, misalignment with text descriptions, and low aesthetic quality. Inspired by the success of Reinforcement Learning with Human Feedback (RLHF) for large language models, prior works collected human-provided scores as feedback on generated images and trained a reward model to improve the T2I generation. In this paper, we enrich the feedback signal by (i) marking image regions that are implausible or misaligned with the text, and (ii) annotating which words in the text prompt are misrepresented or missing on the image. We collect such rich human feedback on 18K generated images (RichHF 18K) and train a multimodal transformer to predict the rich feedback automatically. We show that the predicted rich human feedback can be leveraged to improve image gener ation, for example, by selecting high-quality training data to finetune and improve the generative models, or by cre ating masks with predicted heatmaps to inpaint the prob lematic regions. Notably, the improvements generalize to models (Muse) beyond those used to generate the images on which human feedback data were collected (Stable Dif fusion variants). The RichHF-18K data set will be released soon.'
# # q = 'Title_1: On the Limits of Applying Graph Transformers for Brain Connectome   Classification\nTitle_2: Recognizing and Realizing Temporal Reachability Graphs\nTitle_3: A simple criterion for the uniruledness of an orthogonal modular variety\nTitle_4: Agentic Keyframe Search for Video Question Answering\nTitle_5: Deep Feynman-Kac Methods for High-dimensional Semilinear Parabolic   Equations: Revisit\nTitle_6: The Change You Want To Detect: Semantic Change Detection In Earth   Observation With Hybrid Data Generation\nTitle_7: Age of Information in Multi-Relay Networks with Maximum Age Scheduling\nTitle_8: Distribution of $θ-$powers and their sums\nTitle_9: Fractionally charged Weyl spinors as the bases for elementary particles\nTitle_10: Towards a definition of a meteor cluster: Detection of meteor clusters   from meteor orbit databases\nTitle_11: Null tests with Gaussian Process\nTitle_12: Improving Autoregressive Image Generation through Coarse-to-Fine Token   Prediction\nTitle_13: Surface quasigeostrophic turbulence: The refined study of an active   scalar\nTitle_14: Revisiting the SATIRE-S irradiance reconstruction: Heritage of Mt Wilson   magnetograms and Ca II K observations\nTitle_15: A Cousin Complex for the Quantum Projective Space\nTitle_16: On conservative algebras of 2-dimensional Algebras\nTitle_17: Simple $3$-designs of $\mathrm{PSL}(2,2^n)$ with block size $13$\nTitle_18: BaZrS$_\text{3}$ Lights Up: The Interplay of Electrons, Photons, and   Phonons in Strongly Luminescent Single Crystals\nTitle_19: M2N2V2: Multi-Modal Unsupervised and Training-free Interactive   Segmentation\nTitle_20: MASH-VLM: Mitigating Action-Scene Hallucination in Video-LLMs through   Disentangled Spatial-Temporal Representations'
q = "请分析当前人工智能发展的趋势，并提供相关研究文献。"
data = {
        "query": f"{q}",
        "temperature": 0.7,
        "stream": False,
        "model_name": "chatglm3-6b",
        # "prompt_name": "research_assistant",
        # "prompt_name": "research_question_generator",
        "prompt_name": "ai_expert_grok3",
}


response = requests.post(f"{base_url}/chat", json=data, stream=False)
ans = ""
for line in response.iter_lines():
    decoded_line = line.decode('utf-8')
    if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
        continue
# print(decoded_line)
    if decoded_line.startswith('data'):
        data = json.loads(decoded_line.replace('data: ', ''))
        ans += data['text']
ans_json = ans.replace('\n', '')
json_data = json.loads(ans_json)
formatted_json = json.dumps(json_data, ensure_ascii=False, indent=2)
print("原文: ", q)
print("判断: ", ans)
print(type(json_data), json_data)
print(json_data.get("搜索引擎专家大模型"))


# q = "请提供明天北京天气。"
data = {
        "query": f"{q}",
        "temperature": 0.7,
        "stream": False,
        "model_name": "chatglm3-6b",
        # "prompt_name": "research_assistant",
        # "prompt_name": "research_question_generator",
        "prompt_name": "ai_expert_gpt",
}


response = requests.post(f"{base_url}/chat", json=data, stream=False)
ans = ""
for line in response.iter_lines():
    decoded_line = line.decode('utf-8')
    if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
        continue
# print(decoded_line)
    if decoded_line.startswith('data'):
        data = json.loads(decoded_line.replace('data: ', ''))
        ans += data['text']
ans_json = ans.replace('\n', '')
json_data = json.loads(ans_json)
formatted_json = json.dumps(json_data, ensure_ascii=False, indent=2)
print("原文: ", q)
print("判断: ", ans)
print(type(json_data), json_data)
print(json_data.get("搜索引擎专家大模型"))

data = {
        "query": f"{q}",
        "temperature": 0.7,
        "stream": False,
        "model_name": "chatglm3-6b",
        # "prompt_name": "research_assistant",
        # "prompt_name": "research_question_generator",
        "prompt_name": "ai_expert_deepseek",
}


response = requests.post(f"{base_url}/chat", json=data, stream=False)
ans = ""
for line in response.iter_lines():
    decoded_line = line.decode('utf-8')
    if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
        continue
# print(decoded_line)
    if decoded_line.startswith('data'):
        data = json.loads(decoded_line.replace('data: ', ''))
        ans += data['text']
ans_json = ans.replace('\n', '')
json_data = json.loads(ans_json)
formatted_json = json.dumps(json_data, ensure_ascii=False, indent=2)
print("原文: ", q)
print("判断: ", ans)
print(type(json_data), json_data)
print(json_data.get("搜索引擎专家大模型"))