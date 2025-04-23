import requests
import re, json

base_url = "http://10.2.16.28:2334/chat"
# q= 'Recent Text-to-Image (T2I) generation models such as Stable Diffusion and Imagen have made significant progress in generating high-resolution images based on text descrip tions. However, many generated images still suffer from issues such as artifacts/implausibility, misalignment with text descriptions, and low aesthetic quality. Inspired by the success of Reinforcement Learning with Human Feedback (RLHF) for large language models, prior works collected human-provided scores as feedback on generated images and trained a reward model to improve the T2I generation. In this paper, we enrich the feedback signal by (i) marking image regions that are implausible or misaligned with the text, and (ii) annotating which words in the text prompt are misrepresented or missing on the image. We collect such rich human feedback on 18K generated images (RichHF 18K) and train a multimodal transformer to predict the rich feedback automatically. We show that the predicted rich human feedback can be leveraged to improve image gener ation, for example, by selecting high-quality training data to finetune and improve the generative models, or by cre ating masks with predicted heatmaps to inpaint the prob lematic regions. Notably, the improvements generalize to models (Muse) beyond those used to generate the images on which human feedback data were collected (Stable Dif fusion variants). The RichHF-18K data set will be released soon.'
# q = 'Title_1: On the Limits of Applying Graph Transformers for Brain Connectome   Classification\nTitle_2: Recognizing and Realizing Temporal Reachability Graphs\nTitle_3: A simple criterion for the uniruledness of an orthogonal modular variety\nTitle_4: Agentic Keyframe Search for Video Question Answering\nTitle_5: Deep Feynman-Kac Methods for High-dimensional Semilinear Parabolic   Equations: Revisit\nTitle_6: The Change You Want To Detect: Semantic Change Detection In Earth   Observation With Hybrid Data Generation\nTitle_7: Age of Information in Multi-Relay Networks with Maximum Age Scheduling\nTitle_8: Distribution of $θ-$powers and their sums\nTitle_9: Fractionally charged Weyl spinors as the bases for elementary particles\nTitle_10: Towards a definition of a meteor cluster: Detection of meteor clusters   from meteor orbit databases\nTitle_11: Null tests with Gaussian Process\nTitle_12: Improving Autoregressive Image Generation through Coarse-to-Fine Token   Prediction\nTitle_13: Surface quasigeostrophic turbulence: The refined study of an active   scalar\nTitle_14: Revisiting the SATIRE-S irradiance reconstruction: Heritage of Mt Wilson   magnetograms and Ca II K observations\nTitle_15: A Cousin Complex for the Quantum Projective Space\nTitle_16: On conservative algebras of 2-dimensional Algebras\nTitle_17: Simple $3$-designs of $\mathrm{PSL}(2,2^n)$ with block size $13$\nTitle_18: BaZrS$_\text{3}$ Lights Up: The Interplay of Electrons, Photons, and   Phonons in Strongly Luminescent Single Crystals\nTitle_19: M2N2V2: Multi-Modal Unsupervised and Training-free Interactive   Segmentation\nTitle_20: MASH-VLM: Mitigating Action-Scene Hallucination in Video-LLMs through   Disentangled Spatial-Temporal Representations'
# data = {
#         "query": f"{q}",
#         "temperature": 0.9,
#         "stream": False,
#         "model_name": "chatglm3-6b",
#         # "prompt_name": "research_assistant",
#         # "prompt_name": "research_question_generator",
#         "prompt_name": "research_interest_predictor",
# }


# response = requests.post(f"{base_url}/chat", json=data, stream=False)
# ans = ""
# for line in response.iter_lines():
#     decoded_line = line.decode('utf-8')
#     if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
#         continue
# # print(decoded_line)
#     if decoded_line.startswith('data'):
#         data = json.loads(decoded_line.replace('data: ', ''))
#         ans += data['text']

# # print("原文: ", q)
# print("译文: ", ans)

url = "http://10.2.16.28:2334/knowledge_base/upload_temp_docs"

# # 准备数据字典，根据实际需求填写具体值
# data = {
#     "knowledge_id": "your_knowledge_id",       # 替换为实际的 knowledge_id
#     "chunk_size": 1024,                        # 替换为实际的 chunk_size
#     "chunk_overlap": 100,                      # 替换为实际的 chunk_overlap
#     "zh_title_enhance": True,                  # 替换为实际的 zh_title_enhance，可能是 True/False 或其他值
# }

# 准备文件，使用二进制模式打开文件
files = [
    ("files", ("22371212_郑广懿_模块1_问题与背景__第一版.pdf", open("/usr/zjq/test_file/22371212_郑广懿_模块1_问题与背景__第一版.pdf", "rb"), "application/vnd.openxmlformats-officedocument.presentationml.presentation"))
]

# # # 发送 POST 请求
response = requests.post(url,files=files)
print(response.text)

# # # tmp_kb_id = response.json()['data']['id']
tmp_kb_id =  "tmplrhylbsi"
# # # # print(response.text)
# # # #tmpopkivjk0
# # # # 输出响应信息
data = {
        # "query": "请以专业学术翻译员的身份，严格遵循以下要求将论文2024-CVPR-Rich Human Feedback for Text-to-Image Generation.pdf 的Abstract部分翻译为中文：\n1. **术语精准性**：技术术语须采用《计算机视觉与模式识别领域中文术语规范（2023版）》标准译法，如\"diffusion model\"统一译为\"扩散模型\"，\"human feedback\"译为\"人类反馈\"，未列明术语需结合上下文推导\n2. **句式结构化**：保留原文的学术表达结构，特别是方法描述（\"we propose...\"→\"本文提出...\"）、实验结论（\"demonstrate\"→\"实验证明\"）等关键句式\n3. **学术规范性**：\n- 括号引用保持[1]格式不转换\n- 数学符号保持原格式\n- 专有名词如AdamW不翻译\n- 计量单位保留原文格式（如256×256）\n4. **可逆性要求**：翻译后的中文需确保可通过反向翻译完整还原原文技术细节\n5. **分段处理**：请对以下文本进行逐句翻译，用||分隔原文与译文：\n特别处理以下易错点：\n- \"feedback loop\" → 根据语境选择\"反馈循环\"（系统结构）或\"反馈回路\"（算法流程）\n- \"reward modeling\" → 奖励建模（不译作\"报酬模型\"）\n- 出现\"CLIP\"时需保留大写不翻译 -字数不少于1000字",
        "query": "介绍这篇文章摘要的主要内容",
        "knowledge_id": tmp_kb_id,
        "temperature": 0.7,
        "stream": True,
        "model_name": "chatglm3-6b",
        # "prompt_name": "translate",
}

# # data = {
# #         # "query": "请以专业学术翻译员的身份，严格遵循以下要求将论文2024-CVPR-Rich Human Feedback for Text-to-Image Generation.pdf 的Abstract部分翻译为中文：\n1. **术语精准性**：技术术语须采用《计算机视觉与模式识别领域中文术语规范（2023版）》标准译法，如\"diffusion model\"统一译为\"扩散模型\"，\"human feedback\"译为\"人类反馈\"，未列明术语需结合上下文推导\n2. **句式结构化**：保留原文的学术表达结构，特别是方法描述（\"we propose...\"→\"本文提出...\"）、实验结论（\"demonstrate\"→\"实验证明\"）等关键句式\n3. **学术规范性**：\n- 括号引用保持[1]格式不转换\n- 数学符号保持原格式\n- 专有名词如AdamW不翻译\n- 计量单位保留原文格式（如256×256）\n4. **可逆性要求**：翻译后的中文需确保可通过反向翻译完整还原原文技术细节\n5. **分段处理**：请对以下文本进行逐句翻译，用||分隔原文与译文：\n特别处理以下易错点：\n- \"feedback loop\" → 根据语境选择\"反馈循环\"（系统结构）或\"反馈回路\"（算法流程）\n- \"reward modeling\" → 奖励建模（不译作\"报酬模型\"）\n- 出现\"CLIP\"时需保留大写不翻译 -字数不少于1000字",
# #         "query": "请分析2024-CVPR-Rich Human Feedback for Text-to-Image Generation.pdf解决了什么问题",
# #         "knowledge_id": tmp_kb_id,
# #         "temperature": 0.7,
# #         "stream": True,
# #         "model_name": "chatglm3-6b",
# #         # "prompt_name": "translate",
# # }

# response = requests.post(f"{base_url}/file_chat", json=data, stream=False)

# ai_reply = ""
# origin_docs = []
# # print(response)
# for line in response.iter_lines():
#     if line:
#         decoded_line = line.decode('utf-8')
#         if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
#             continue
#         if decoded_line.startswith('data'):
#             data = decoded_line.replace('data: ', '')
#             data = json.loads(data)
#             if "answer" in data:
#                 ai_reply += data["answer"]
#             if "docs" in data:
#                 for doc in data["docs"]:
#                     doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
#                     origin_docs.append(doc)

# print("回复：", ai_reply)
# print("docs: ", origin_docs)

# result_answer = ""
# docs = []
# for line in response.iter_content(None, decode_unicode=True):
#     # print(line)
#     if line.startswith("data: "):
#         json_str = line[len("data: "):]
#         try:
#             data = json.loads(json_str)  # 解析 JSON
#             if "answer" in data:
#                 result_answer += data["answer"]  # 提取并合并 answer 字段
#             elif "docs" in data:
#                 docs.extend(data["docs"])  # 合并 docs 列表
#         except json.JSONDecodeError:
#             print(f"无法解析 JSON: {line}")

# # 输出合并后的 answer 字符串
# print("合并的 Answer:", result_answer)

# # 输出合并后的 docs 列表
# print("\n合并的 Docs:")
# for doc in docs:
#     print(doc)
    


