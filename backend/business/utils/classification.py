'''
    文献子类划分，每篇文献允许拥有多个子类
'''
import json
import os
import requests
import torch
from django.conf import settings

# 注入子类
# 导入模型
from business.models.paper import *
from tqdm import tqdm

title_json_path = os.path.join(settings.MEDIA_ROOT, "title.json")
abstract_json_path = os.path.join(settings.MEDIA_ROOT, "abstract.json")

def embed_for_subclass(texts):
    if not isinstance(texts, list):
        texts = [texts]

    url = f'http://{settings.REMOTE_MODEL_BASE_PATH}/other/embed_texts'
    payload = json.dumps({
        "texts": texts
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()['data']

def embed_from_file(file_path):
    url = f'http://10.2.16.28/upload'
    with open(file_path, 'rb') as file:
        files = {"files": (file_path, file, "application/json")}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()  # 如果响应状态码不是 2xx，会抛出异常
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    return response.json()['data']

def create_labels():
    # 创建新的 Label 实例
    names = ["边缘检测", "目标检测", "图像分类", "图像去噪", "图像分割", "人脸识别", "姿态估计", "动作识别", "人群计数", "医学影像", "三维重建", "对抗样本攻击"]
    for name in names:
        label = Subclass.objects.create(name=name)
        label.save()


def dump_titles_and_abstracts():
    papers = Paper.objects.all()
    # 统一嵌入
    titles = []
    abstracts = []
    for paper in tqdm(papers):
        # 获取 Paper 的 Title 和 Abstract
        title = paper.title
        abstract = paper.abstract
        titles.append(title)
        abstracts.append(abstract)
    payload_title = json.dumps({"texts": titles})
    payload_abstract = json.dumps({"texts": abstracts})
    headers = {"Content-Type": "application/json"}
    with open(title_json_path, 'w', encoding='utf-8') as f:
        f.write(payload_title)
    with open(abstract_json_path, 'w', encoding='utf-8') as f:
        f.write(payload_abstract)
    print('dump titles and abstracts over!')

def delete_all_subclasses():
    # papers = Paper.objects.all()
    # for paper in tqdm(papers):
    #     paper.sub_classes.clear()
    #     paper.save()
    Subclass.objects.all().delete()
'''
    分类思路：
        1. 将所有子类嵌入，与每篇论文的Title和Abstract分别计算余弦相似度
        2. 根据人工观察，Title或Abstract任一相似度大于0.4即可认为满足子类划分
        3. 若一篇论文依2方法无法获得任一子类，将相似度最大的子类作为子类划分
'''

def classify():
    # 获取所有 Subclass 实体
    subclasses = Subclass.objects.all()

    # 计算每个 Subclass 名称的嵌入向量
    subclass_embeddings = {subclass: embed_for_subclass(subclass.name) for subclass in subclasses}
    # print(subclass_embeddings)
    # assert 1 == 0
    # 获取所有 Paper 实体

    papers = Paper.objects.all()
    title_embeddings = embed_from_file(title_json_path)
    print("Title embedding over!")
    abstract_embeddings = embed_for_subclass(abstract_json_path)
    print("Abstract embedding over!")

    for i, paper in tqdm(enumerate(papers)):
        # 遍历所有 Subclass，计算相似度
        max_sim = torch.tensor(0.0)
        cur_subclass = None
        cur_flag = 0
        for subclass, subclass_embedding in subclass_embeddings.items():
            title_similarity = torch.tensor(subclass_embedding).view(1, -1).mm(torch.tensor(title_embeddings[i]).view(-1, 1)).flatten()[0]
            abstract_similarity = torch.tensor(subclass_embedding).view(1, -1).mm(torch.tensor(abstract_embeddings[i]).view(-1, 1)).flatten()[0]
            if title_similarity > 0.5 or abstract_similarity > 0.5:
                # 将 Subclass 加入到 Paper 的 ManyToMany 属性中
                cur_flag = 1
                paper.sub_classes.add(subclass)
            if max_sim < title_similarity + abstract_similarity:
                max_sim = title_similarity + abstract_similarity
                cur_subclass = subclass

        # 如果一类都找不到，默认将相似度最大的作为子类标签
        if cur_flag != 1:
            paper.sub_classes.add(cur_subclass)

        # 保存 Paper 实体
        paper.save()



from django.views.decorators.http import require_http_methods
from business.utils import reply
@require_http_methods(["POST"])
def init_classification(request):
    delete_all_subclasses()
    create_labels()
    dump_titles_and_abstracts()
    classify()
    return reply.success({"success": "成功"})


if __name__ == '__main__':
    # delete_all_subclasses()
    # create_labels()
    # classify()
    dict1 = dict({
        "a": {
            "b": 100
        },
        "y": 200
    })
    dict2 = dict({
        "a": {
            "c": 200
        },
        "z": 400
    })
    dict1.update(dict2)
    print(dict1)