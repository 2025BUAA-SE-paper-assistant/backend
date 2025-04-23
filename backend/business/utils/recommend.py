import requests
import re, json
import pandas as pd
from business.models import User, Paper, FileReading
from business.api.search import do_dialogue_search
from django.conf import settings
from django.core.cache import cache
import random

def get_personal_papers(user):
    '''根据5:3:2的比例从user.collected_paper,user.liked_paper,FileReading(user_id=user.id)
    里随机抽取20篇论文，如果相关论文不足则从数据库中随机抽取
    '''
    collected_papers = user.collected_papers.all()
    liked_papers = user.liked_papers.all()
    filereadings = FileReading.objects.filter(user_id=user.user_id, paper_id__isnull=False)
    readed_papers_id = filereadings.values_list('paper_id', flat=True)
    readed_papers = Paper.objects.filter(paper_id__in=readed_papers_id)

    collected_size = min(10, len(collected_papers))
    liked_size = min(6, len(liked_papers))
    filereading_size = min(4, len(filereadings))
    papers = list(collected_papers)[:collected_size] + list(liked_papers)[:liked_size] + list(readed_papers)[:filereading_size]
    if len(papers) == 0:
        # 随机抽20篇
        all_papers = list(Paper.objects.all())
        papers = random.sample(all_papers, min(20, len(all_papers)))
    
    return papers

    
    

def question_2_paper(question):
    chat_chat_url = f"http://{settings.REMOTE_MODEL_BASE_PATH}/chat/chat"
    headers = {"Content-Type": "application/json"}
    papers = do_dialogue_search(question, chat_chat_url, headers)
    return papers

def get_personal_questions(user):
    '''
    根据用户喜好推荐问题
    '''
    papers = get_personal_papers(user)
    content = ""
    for i, paper in enumerate(papers, 1):
        # print("Title:", row['title'])
        # print("Abstract:", row['abstract'])
        # print("-" * 50)  # 分隔线
        content += f"Title_{i}: {paper.title}\nAbstrastract_{i}: {paper.abstract}\n"

    base_url = "http://10.2.16.28:2334/chat" #ai URL
    # q= 'Recent Text-to-Image (T2I) generation models such as Stable Diffusion and Imagen have made significant progress in generating high-resolution images based on text descrip tions. However, many generated images still suffer from issues such as artifacts/implausibility, misalignment with text descriptions, and low aesthetic quality. Inspired by the success of Reinforcement Learning with Human Feedback (RLHF) for large language models, prior works collected human-provided scores as feedback on generated images and trained a reward model to improve the T2I generation. In this paper, we enrich the feedback signal by (i) marking image regions that are implausible or misaligned with the text, and (ii) annotating which words in the text prompt are misrepresented or missing on the image. We collect such rich human feedback on 18K generated images (RichHF 18K) and train a multimodal transformer to predict the rich feedback automatically. We show that the predicted rich human feedback can be leveraged to improve image gener ation, for example, by selecting high-quality training data to finetune and improve the generative models, or by cre ating masks with predicted heatmaps to inpaint the prob lematic regions. Notably, the improvements generalize to models (Muse) beyond those used to generate the images on which human feedback data were collected (Stable Dif fusion variants). The RichHF-18K data set will be released soon.'
    headers = {
        'Content-Type': 'application/json'
    }
    #data部分除了query写死
    data = {
        "query": f"{content}", # 原文
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
        recommend_questions.append(question+'?')
    return(recommend_questions)


def get_personal_key(user):
    return f'recommendation_{user.user_id}'

def set_personal_recommend_cache(user):
    '''将基于用户的推荐问题以及推荐文献写入缓存,缓存一天'''
    questions = get_personal_questions(user)
    cached_data = [
        {
            "question": question,
            "paper_ids": [paper.id for paper in get_personal_papers(user)],
        }
        for question in questions
    ]
    cache_key = get_personal_key(user)
    cache.set(cache_key, cached_data, timeout=24 * 60 * 60)  # 缓存一天

import logging
def set_all_personal_recommend_cache():
    users = User.objects.all()
    max_retries = 3  # 最大重试次数
    for user in users:
        for attempt in range(max_retries):
            try:
                set_personal_recommend_cache(user)
                logging.info(f"Successfully set cache for user {user.user_id}")
                break  # 如果成功，跳出重试循环
            except Exception as e:
                logging.error(f"Error setting cache for user {user.user_id}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to set cache for user {user.user_id} after {max_retries} attempts.")

