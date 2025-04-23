import json
import os.path

import numpy as np
import faiss
import pickle

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from wrap.content import validate_content
from business.models import Paper
from business.utils import reply


def get_all_paper():
    papers = Paper.objects.all()
    for paper in papers:
        keyword = paper.title + "." + paper.abstract
        paper_id = paper.paper_id
        yield keyword, paper_id

def false_embed(texts):
    if not isinstance(texts, list):
        texts = [texts]
    url = "http://10.2.16.28:2336/upload"
    # json_file_path = "/usr/zjq/payload_output.json"
    json_file_path = "payload_output.json"
    with open('test.json', 'w') as wf:
        json.dump({}, wf)
    # 打开文件并发送POST请求
    with open(json_file_path, "rb") as file:
        files = {"files": (json_file_path, file, "application/json")}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()  # 如果响应状态码不是 2xx，会抛出异常
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    return response.json()["data"]

def embed(texts):
    if not isinstance(texts, list):
        texts = [texts]

    url = f"http://{settings.REMOTE_MODEL_BASE_PATH}/other/embed_texts"
    payload = json.dumps({"texts": texts})
    with open("payload_output.json", "w", encoding="utf-8") as f:
        f.write(payload)
    headers = {"Content-Type": "application/json"}
    session = requests.Session()

    # 设置重试策略
    retries = Retry(
        total=300,  # 总重试次数
        backoff_factor=1,  # 重试间隔时间的增长因子（1秒，2秒，4秒...）
        status_forcelist=[500, 502, 503, 504],  # 针对哪些 HTTP 状态码进行重试
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    # 发送请求并设置超时时间
    try:
        response = session.post(
            url, headers=headers, data=payload, timeout=(30, 120)
        )  # 超时时间为 60 秒
        response.raise_for_status()  # 如果响应状态码不是 2xx，会抛出异常
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    return response.json()["data"]


def local_vdb_init(request):
    d = settings.VECTOR_DIM

    # db_vectors = np.random.random((nb, d)).astype('float32')
    texts = []
    metadata = []
    for keyword, paper_id in get_all_paper():
        texts.append(keyword)
        metadata.append(paper_id)
    # embed_texts = embed(texts)
    embed_texts = false_embed(texts)
    db_vectors = np.array(embed_texts).astype(np.float32)

    # 创建索引
    index = faiss.IndexFlatL2(d)  # 使用 L2 距离
    print("Is index trained?", index.is_trained)  # 对于 IndexFlatL2，总是 True

    # 添加向量到索引
    index.add(db_vectors)

    # 打印结果
    # for i in range(nq):
    #     print(f"Query {i}:")
    #     for j in range(k):
    #         print(f"  Neighbor {j}: ID = {indices[i, j]}, Distance = {distances[i, j]}, Metadata = {metadata[indices[i, j]]}")

    # 保存索引和元数据
    print(os.path.join(settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_FAISS_NAME))
    faiss.write_index(
        index,
        os.path.join(settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_FAISS_NAME),
    )
    os.makedirs(
        os.path.join(settings.LOCAL_VECTOR_DATABASE_PATH),
        exist_ok=True,
    )
    with open(
        os.path.join(settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_METADATA_NAME),
        "wb",
    ) as f:
        pickle.dump(metadata, f)

    return reply.success({"success": "成功"})


def get_filtered_paper(text, k, threshold=None):
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    faiss_path = os.path.join(
        settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_FAISS_NAME
    )
    metadata_path = os.path.join(
        settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_METADATA_NAME
    )

    index = faiss.read_index(faiss_path)
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)

    embed_texts = embed(text)
    print(embed_texts)
    distances, indices = index.search(np.array(embed_texts).astype(np.float32), k)
    i2d_dict = {}
    for d, i in zip(distances[0], indices[0]):
        i2d_dict[metadata[i]] = d
    paper_ids = [metadata[i] for i in indices[0]]
    filtered_papers = Paper.objects.filter(paper_id__in=paper_ids)
    ht_threshold_papers = []
    for p in filtered_papers:
        sim = i2d_dict[p.paper_id]
        if threshold is not None and sim < threshold:
            continue
        # p_dict = p.to_dict()
        # p_dict['similarity'] = float(sim)
        ht_threshold_papers.append(p)
    return ht_threshold_papers

@validate_content(fields=["texts"])
def easy_vector_query(request):
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    # 1. 加载索引和元数据(是否可在初始化中加载) 2. 进行查询
    index = faiss.read_index(
        os.path.join(settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_FAISS_NAME)
    )
    with open(
        os.path.join(settings.LOCAL_VECTOR_DATABASE_PATH, settings.LOCAL_METADATA_NAME),
        "rb",
    ) as f:
        metadata = pickle.load(f)

    request_data = json.loads(request.body)
    texts = request_data["texts"]
    k = request_data["k"]
    if not k:
        k = 20
    if not isinstance(texts, list):
        texts = [texts]

    embed_texts = embed(texts)

    # 查找，返回相似论文
    # distances: [1, K], indices: [1, k]
    distances, indices = index.search(np.array(embed_texts).astype(np.float32), k)
    i2d_dict = {}
    for d, i in zip(distances[0], indices[0]):
        i2d_dict[metadata[i]] = d
    paper_ids = [metadata[i] for i in indices[0]]
    filtered_paper = Paper.objects.filter(paper_id__in=paper_ids)
    paper_dict = []
    for p in filtered_paper:
        p_dict = p.to_dict()
        p_dict["similarity"] = float(i2d_dict[p.paper_id])
        print(p_dict)
        paper_dict.append(p_dict)

    return reply.success({"papers": paper_dict})
