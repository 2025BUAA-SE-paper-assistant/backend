"""
本文件的功能是文献阅读助手，给定一篇文章进行阅读，根据问题的答案进行回答。
API格式如下：
api/peper_interpret/...
"""

import asyncio
import datetime
import json, ast
import logging
import os
import re
from urllib.parse import quote
import requests
from django.views.decorators.http import require_http_methods

from django.conf import settings
from business.models import UserDocument, FileReading, Paper, User
from business.utils import reply

from business.utils.download_paper import downloadPaper

import asyncio
import aiohttp
import json
import re
from django.http import StreamingHttpResponse

# 论文研读模块

"""
    创建文献研读对话：
        上传一个文件，开启一个研读对话，返回 tmp_kb_id

    对话记录方式为: [
        {"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"},
        {"role": "assistant", "content": "虎头虎脑"},
    ]
"""


def create_content_disposition(filename):
    """构建适用于Content-Disposition的filename和filename*参数"""
    # URL 编码文件名
    safe_filename = quote(filename)
    # 构建Content-Disposition头部
    disposition = f'form-data; name="file"; filename="{filename}"; filename*=UTF-8\'\'{safe_filename}'
    return disposition


# 删除Tmp_kb的缓存，用于某tmp_kb_id再也不被使用时，避免内存爆炸
def delete_tmp_kb(tmp_kb_id):
    delete_tmp_kb_url = (
        f"http://{settings.REMOTE_MODEL_BASE_PATH}/knowledge_base/delete_temp_docs"
    )
    # headers = {
    #     'Content-Type': 'application/x-www-form-urlencoded'
    # }
    payload = {"knowledge_id": tmp_kb_id}
    response = requests.post(delete_tmp_kb_url, data=payload)  # data默认是form形式
    if response.status_code == 200:
        return True
    else:
        return False


# 建立file_reading和tmp_kb的映射
def insert_file_2_kb(file_reading_id, tmp_kb_id):
    """建立file_reading和tmp_kb的映射"""
    if not os.path.exists(settings.USER_READ_MAP_PATH):
        os.makedirs(os.path.dirname(settings.USER_READ_MAP_PATH), exist_ok=True)

    with open(settings.USER_READ_MAP_PATH, "r") as f:
        f_2_kb_map = json.load(f)
    if file_reading_id in f_2_kb_map:
        if delete_tmp_kb(f_2_kb_map[file_reading_id]):
            print("删除TmpKb成功")
        else:
            print("删除TmpKb失败")

    f_2_kb_map[file_reading_id] = tmp_kb_id
    with open(settings.USER_READ_MAP_PATH, "w") as f:
        json.dump(f_2_kb_map, f, indent=4)


def get_tmp_kb_id(file_reading_id):
    """获取tmp_kb_id"""

    os.makedirs(os.path.dirname(settings.USER_READ_MAP_PATH), exist_ok=True)

    with open(settings.USER_READ_MAP_PATH, "r") as f:
        f_2_kb_map = json.load(f)
    # print(f_2_kb_map)
    if str(file_reading_id) in f_2_kb_map:
        return f_2_kb_map[str(file_reading_id)]
    else:
        return None


@require_http_methods(["POST"])
def create_paper_study(request):
    # 鉴权
    username = request.session.get("username")
    print(request.session)
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!username: {username}")
    if username is None:
        username = "sanyuba"
    print(username)
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")

    # 处理请求头
    request_data = json.loads(request.body)
    file_type = request_data.get("file_type")  # 1代表上传文献研读, 2代表已有文件研读
    title, content_type, local_path, file_reading = None, None, None, None
    if file_type == 1:
        document_id = request_data.get("document_id")
        # 获取文件, 后续支持直接对8k篇论文进行检索
        document = UserDocument.objects.get(document_id=document_id)
        # 获取服务器本地的path
        local_path = document.local_path
        content_type = document.format
        title = document.title
        # 先查找数据库是否有对应的Filereading
        file_readings = FileReading.objects.filter(document_id=document_id)
        if file_readings.count() == 0:
            # 创建一段新的filereading对话, 并设置conversation对话路径，创建json文件
            file_reading = FileReading(
                user_id=user,
                document_id=document,
                title="上传论文研读",
                conversation_path=None,
            )
        elif file_readings.count() >= 1:
            file_reading = file_readings.first()
        else:
            return reply.fail(msg="一个用户上传文件存在多个文献研读文件，逻辑有误")
    elif file_type == 2:
        paper_id = request_data.get("paper_id")
        paper = Paper.objects.get(paper_id=paper_id)
        title = paper.title
        content_type = ".pdf"
        local_path = get_paper_local_url(paper)
        if local_path is None:
            return reply.fail(msg="论文无法下载，请联系管理员/换一篇文章研读")
        file_reading = FileReading(
            user_id=user, paper_id=paper, title="数据库论文研读", conversation_path=None
        )
    else:
        return reply.fail(msg="类型有误, 金哥我阐述你的梦")

    file_reading.save()
    conversation_path = os.path.join(
        settings.USER_READ_CONSERVATION_PATH, str(file_reading.id) + ".json"
    )
    file_reading.conversation_path = conversation_path
    file_reading.save()
    # if os.path.exists(conversation_path):
    #     os.remove(conversation_path)


    with open(conversation_path, "w") as f:
        json.dump({"conversation": []}, f, indent=4)

    with open(conversation_path, "r") as f:
        history = json.load(f)

    # 上传到远端服务器, 创建新的临时知识库
    upload_temp_docs_url = (
        f"http://{settings.REMOTE_MODEL_BASE_PATH}/knowledge_base/upload_temp_docs"
    )

    print(open(local_path, "rb"))
    files = [
        (
            "files",
            (
                title + content_type,
                open(local_path, "rb"),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
        )
    ]

    # headers = {
    #     'Content-Type': 'multipart/form-data'
    # }

    response = requests.request("POST", upload_temp_docs_url, files=files)
    # 关闭文件，防止内存泄露
    for k, v in files:
        v[1].close()

    if response.status_code == 200:
        tmp_kb_id = response.json()["data"]["id"]
        insert_file_2_kb(str(file_reading.id), tmp_kb_id)
        return reply.success(
            {"file_reading_id": file_reading.id, "conversation_history": history},
            msg="开启文献研读对话成功",
        )
    else:
        return reply.fail(msg="连接模型服务器失败")


"""
    恢复文献研读对话：
        传入文献研读对话id即可
"""


@require_http_methods(["POST"])
def restore_paper_study(request):
    # 鉴权
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")

    # 获取filereading与文件路径，重新上传给服务器开启对话
    request_data = json.loads(request.body)
    file_reading_id = request_data.get("file_reading_id")
    fr = FileReading.objects.get(id=file_reading_id)
    if not fr.document_id:
        paper = Paper.objects.get(paper_id=fr.paper_id.get_paper_id())
        local_path = paper.local_path
        title = paper.title
        content_type = ".pdf"
    else:
        document = UserDocument.objects.get(
            document_id=fr.document_id.get_document_id()
        )
        local_path = document.local_path
        title = document.title
        content_type = document.format

    if local_path is None or title is None:
        return reply.fail(msg="服务器内无本地文件, 请检查")

    # 上传到远端服务器, 创建新的临时知识库
    upload_temp_docs_url = (
        f"http://{settings.REMOTE_MODEL_BASE_PATH}/knowledge_base/upload_temp_docs"
    )
    files = [
        (
            "files",
            (
                title + content_type,
                open(local_path, "rb"),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
        )
    ]

    # headers = {
    #     'Content-Type': 'multipart/form-data'
    # }

    response = requests.request("POST", upload_temp_docs_url, files=files)
    # 关闭文件，防止内存泄露
    for k, v in files:
        v[1].close()

    # 返回结果, 需要将历史对话一起返回
    if response.status_code == 200:
        tmp_kb_id = response.json()["data"]["id"]
        insert_file_2_kb(str(file_reading_id), tmp_kb_id)
        # 若删除过历史对话, 则再创建一个文件
        if not os.path.exists(fr.conversation_path):
            os.makedirs(os.path.dirname(fr.conversation_path), exist_ok=True)
            with open(fr.conversation_path, "w") as f:
                json.dump({"conversation": []}, f, indent=4)

        # 读取历史对话记录
        with open(fr.conversation_path, "r") as f:
            conversation_history = json.load(
                f
            )  # 使用 json.load() 方法将 JSON 数据转换为字典

        return reply.success(
            {
                "file_reading_id": file_reading_id,
                "conversation_history": conversation_history,
            },
            msg="恢复文献研读对话成功",
        )
    else:
        return reply.fail(msg="连接模型服务器失败")


@require_http_methods(["POST"])
def get_paper_study(request):
    # 鉴权
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")
    # 处理请求头
    request_data = json.loads(request.body)
    file_type = request_data.get("file_type")  # 1代表上传文献研读, 2代表已有文件研读
    title, content_type, local_path, file_reading = None, None, None, None
    if file_type == 1:
        # 先查找数据库是否有对应的Filereading
        document_id = request_data.get("document_id")
        try:
            document = UserDocument.objects.get(document_id=document_id)
        except UserDocument.DoesNotExist:
            return reply.fail(msg="没有该上传文件记录")
        content_type = document.format
        title = document.title
        local_path = document.local_path
        if local_path is None or title is None:
            return reply.fail(msg="服务器内没有该上传文件")
        file_readings = FileReading.objects.filter(
            document_id=document_id, user_id=user.user_id
        )
        if file_readings.count() == 0:
            # 创建
            file_reading = FileReading(
                user_id=user,
                document_id=document,
                title="上传论文研读",
                conversation_path=None,
            )
        else:
            # 已有记录
            file_reading = file_readings.first()

    elif file_type == 2:
        paper_id = request_data.get("paper_id")
        try:
            paper = Paper.objects.get(paper_id=paper_id)
        except Paper.DoesNotExist:
            return reply.fail(msg="没有该论文记录")
        content_type = '.pdf'
        title = paper.title
        local_path = get_paper_local_url(paper)
        if local_path is None:
            return reply.fail(msg="论文无法下载，请联系管理员/换一篇文章研读")
        file_readings = FileReading.objects.filter(
            paper_id=paper_id, user_id=user.user_id
        )
        if not file_readings:
            # 创建
            file_reading = FileReading(
                user_id=user, paper_id=paper, title="数据库论文研读", conversation_path=None
            )
        else:
            file_reading = file_readings.first()
    file_reading.save() # 内存实体保存到数据库中，获取id
    if file_reading.conversation_path is None or not os.path.exists(file_reading.conversation_path):
        # 新建研读或已有对话历史文件被删除
        conversation_path = os.path.join(
            settings.USER_READ_CONSERVATION_PATH, str(file_reading.id) + ".json"
        )
        file_reading.conversation_path = conversation_path
        os.makedirs(os.path.dirname(file_reading.conversation_path), exist_ok=True)
        with open(file_reading.conversation_path, "w") as f:
            json.dump({"conversation": []}, f, indent=4)

    # 读取历史对话记录
    with open(file_reading.conversation_path, "r") as f:
        # 使用 json.load() 方法将 JSON 数据转换为字典
        history = json.load(f)
    file_reading.save()

    # 上传到远端服务器, 创建新的临时知识库
    upload_temp_docs_url = (
        f"http://{settings.REMOTE_MODEL_BASE_PATH}/knowledge_base/upload_temp_docs"
    )
    files = [
        (
            "files",
            (
                title + content_type,
                open(local_path, "rb"),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
        )
    ]

    response = requests.request("POST", upload_temp_docs_url, files=files)
    # 关闭文件，防止内存泄露
    for k, v in files:
        v[1].close()

    if response.status_code == 200:
        tmp_kb_id = response.json()["data"]["id"]
        insert_file_2_kb(str(file_reading.id), tmp_kb_id)
        return reply.success(
            {"file_reading_id": file_reading.id, "conversation_history": history},
            msg="开启文献研读对话成功",
        )
    else:
        return reply.fail(msg="连接模型服务器失败")

"""
    异步测试
"""


@require_http_methods(["POST"])
async def async_test(request):
    print("Task started.")
    await asyncio.sleep(5)  # 模拟异步操作，例如等待 I/O
    print("Task completed.")


# from PyPDF2 import PdfReader
import fitz
def is_pdf_corrupted(file_path,paper):
    try:
        doc = fitz.open(file_path)
        if len(doc) <= 0:
            return True
        # with open(file_path, 'rb') as f:
        #     reader = PdfReader(f)
            # 如果能够成功读取页面数量而不抛出异常，则文件可能正常
            # num_pages = len(reader.pages)

        # 未解析段落分块
        if not paper.paragraph:
            paragrahs = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                blocks = page.get_text("blocks")
                for i, block in enumerate(blocks):
                    block_list = list(block)
                    paragraph_with_page = {
                        "page_num": page_num,
                        "block": block_list
                    }
                    paragrahs.append(json.dumps(paragraph_with_page))
            paper.paragraph = json.dumps(paragrahs)
            paper.save()
        return False  # 文件正常
    except Exception as e:
        # 打印异常信息（可选）
        print(f"文件 {file_path} 可能损坏，错误：{e}")
        return True  # 文件损坏

"""
    获取本地url
"""


def get_paper_local_url(paper):
    local_pdf = paper.local_path
    max_retries = 3
    retries = 0
    while retries < max_retries:
        if local_pdf and os.path.exists(local_pdf):
            # 检查 PDF 文件是否损坏
            if is_pdf_corrupted(local_pdf,paper):
                os.remove(local_pdf)  # 删除损坏的文件
                local_pdf = None
            else:
                return local_pdf  # 文件正常，返回路径

        # 如果文件不存在或者损坏，尝试重新下载
        if not local_pdf:
            original_url = paper.original_url.replace("abs", "pdf")  # 将 URL 中的 "abs" 替换为 "pdf"
            try:
                filename = str(paper.paper_id)
                # 保存到服务器本地路径（假设你有一个存储目录，例如 'pdfs/'）
                try:
                    local_path = downloadPaper(original_url, filename)
                except Exception as e:
                    print(f"下载失败，错误：{e}")
                    retries += 1
                    continue

                # 更新数据库中的 local_path 字段
                paper.local_path = local_path
                paper.save()

                # 再次检查下载的文件是否损坏
                if not is_pdf_corrupted(local_path,paper):
                    return local_path  # 文件正常，返回路径
            except Exception as e:
                print(f"处理 PDF 文件时发生错误：{e}")
                retries += 1
        else:
            retries += 1
    return None  # 如果多次重试都失败，返回 None

"""
    获取文献本地url, 无则下载
"""


def get_paper_url(request):
    # 鉴权
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")

    paper_id = request.GET.get("paper_id")
    paper = Paper.objects.get(paper_id=paper_id)
    paper_local_url = get_paper_local_url(paper)
    if paper_local_url is None:
        return reply.fail(msg="文献下载失败，请检查网络或联系管理员")
    response ={
            "local_url": paper_local_url,
            "paragraph": paper.paragraph,
            "message": "success",
        }
    return reply.success(response, msg="success")

from django.db.models import Q
from tqdm import tqdm
@require_http_methods(['POST'])
def check_all_pdfs(request):
    # 只检查不为空的
    downloaded_papers = Paper.objects.filter(Q(local_path__isnull=False)&~Q(local_path__exact=''))
    paper_not_well = []
    for paper in tqdm(downloaded_papers):
        if get_paper_local_url(paper) is None:
            paper_not_well.append({'id':paper.paper_id,'title':paper.title})
    return reply.success(data={'bad_papers':paper_not_well})




async def do_file_chat(conversation_history, query, tmp_kb_id):
    """
    处理文件聊天请求，流式返回AI回答、引用文档和推荐问题
    """
    # 构建请求URL和头部
    file_chat_url = f"http://{settings.REMOTE_MODEL_BASE_PATH}/chat/file_chat"
    knowledge_base_chat_url = f"http://{settings.REMOTE_MODEL_BASE_PATH}/chat/knowledge_base_chat"
    search_engine_chat_url = f"http://{settings.REMOTE_MODEL_BASE_PATH}/chat/search_engine_chat"
    headers = {"Content-Type": "application/json"}

    # 定义流式处理的生成器
    async def stream_generator():
        # 初始化变量
        ai_reply = ""
        origin_docs = []
        question_reply = []

        # 判断是否有历史对话
        has_history = len(conversation_history) != 0
        print (f"time: {datetime.datetime.now()}")

        # 构建请求载荷
        if has_history:
            payload = json.dumps(
                {
                    "query": query,
                    "knowledge_id": tmp_kb_id,
                    "history": conversation_history[-10:],  # 传10条历史记录
                    "prompt_name": "text_new",  # 使用历史记录对话模式
                    "max_tokens": 2048,
                    "top_k": 10,
                    "stream": True,
                }
            )
        else:
            payload = json.dumps(
                {
                    "query": query,
                    "knowledge_id": tmp_kb_id,
                    "prompt_name": "default",  # 使用普通对话模式
                    "max_tokens": 2048,
                    "top_k": 10,
                    "stream": True,
                }
            )

        # 判断是否需要分发任务
        async def need_distribution():
            data_0 = {
                "query": query,
                "temperature": 0.3,
                "stream": True,
                "model_name": "chatglm3-6b",
                "prompt_name": "ai_expert_grok3",

            }
            payload_0 = json.dumps(data_0)

            async with aiohttp.ClientSession() as session:
                async with session.post(settings.CHAT_CHAT_URL, data=payload_0, headers=headers) as response:
                    ans = ""
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith(': ping'):
                            continue
                        if decoded_line.startswith('data'):
                            data = json.loads(decoded_line.replace('data: ', ''))
                            ans += data['text']

            try:
                ans_json = ans.replace('\n', '')
                json_data = json.loads(ans_json)
                need_2 = json_data.get("搜索引擎专家大模型")
                need_3 = json_data.get("科研大模型")
                return need_2, need_3
            except json.JSONDecodeError:
                return False, False

        # 处理多模型调用
        async def process_multi_models(need_2, need_3):
            # 调用原生大模型
            if has_history:
                data_1 = {
                    "query": query,
                    "knowledge_id": tmp_kb_id,
                    "temperature": 0.3,
                    "stream": True,
                    "model_name": "chatglm3-6b",
                    "history": conversation_history[-10:],
                    "prompt_name": "text_new",
                    "max_tokens": 2048,
                    "top_k": 10,
                }
            else:
                data_1 = {
                    "query": query,
                    "knowledge_id": tmp_kb_id,
                    "temperature": 0.3,
                    "stream": True,
                    "model_name": "chatglm3-6b",
                    "prompt_name": "text_new",
                    "max_tokens": 2048,
                    "top_k": 10,
                }

            # 获取原生大模型回答
            async with aiohttp.ClientSession() as session:
                payload_2 = json.dumps(data_1)
                async with session.post(file_chat_url, data=payload_2, headers=headers) as response:
                    ai_reply_1 = ""
                    origin_docs_1 = []
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith(': ping'):
                            continue
                        if decoded_line.startswith('data'):
                            data = json.loads(decoded_line.replace('data: ', ''))
                            if "answer" in data:
                                ai_reply_1 += data["answer"]
                                # 流式返回原生大模型的部分回答
                                yield {'type': 'answer', 'content': data["answer"], 'source': 'base_model'}
                            if "docs" in data:
                                for doc in data["docs"]:
                                    doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                                    origin_docs_1.append(doc)
                                    # yield {'type': 'doc', 'content': doc, 'source': 'base_model'}

            # 调用搜索引擎
            ai_reply_2 = ""
            origin_docs_2 = []
            if need_2:
                data_2 = {
                    "query": query,
                    "temperature": 0.7,
                    "top_k": 10,
                    "max_tokens": 2048,
                    "search_engine_name": "bing",
                    "model_name": "chatglm3-6b",
                    "prompt_name": "search",
                    "stream": True,
                }

                async with aiohttp.ClientSession() as session:
                    payload_3 = json.dumps(data_2)
                    async with session.post(search_engine_chat_url, data=payload_3, headers=headers) as response:
                        async for line in response.content:
                            decoded_line = line.decode('utf-8').strip()
                            if decoded_line.startswith(': ping'):
                                continue
                            if decoded_line.startswith('data'):
                                data = json.loads(decoded_line.replace('data: ', ''))
                                if "answer" in data:
                                    ai_reply_2 += data["answer"]
                                    yield {'type': 'answer', 'content': data["answer"], 'source': 'search_engine'}
                                if "docs" in data:
                                    for doc in data["docs"]:
                                        doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                                        origin_docs_2.append(doc)
                                        # yield {'type': 'doc', 'content': doc, 'source': 'search_engine'}

            # 调用科研模型
            ai_reply_3 = ""
            origin_docs_3 = []
            if need_3:
                data_3 = {
                    "query": query,
                    "knowledge_base_name": "Paper_all_in_one",
                    "temperature": 0.7,
                    "model_name": "chatglm3-6b",
                    "prompt_name": "literature_research_agent",
                    "max_tokens": 4096,
                    "top_k": 10,
                    "stream": True,
                }

                async with aiohttp.ClientSession() as session:
                    payload_4 = json.dumps(data_3)
                    async with session.post(knowledge_base_chat_url, data=payload_4, headers=headers) as response:
                        async for line in response.content:
                            decoded_line = line.decode('utf-8').strip()
                            if decoded_line.startswith(': ping'):
                                continue
                            if decoded_line.startswith('data'):
                                data = json.loads(decoded_line.replace('data: ', ''))
                                if "answer" in data:
                                    ai_reply_3 += data["answer"]
                                    yield {'type': 'answer', 'content': data["answer"], 'source': 'research_model'}
                                if "docs" in data:
                                    for doc in data["docs"]:
                                        doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                                        origin_docs_3.append(doc)
                                        # yield {'type': 'doc', 'content': doc, 'source': 'research_model'}

            # 整合多个模型的回答
            if has_history:
                data_4 = {
                    "query": f"原生模型输出：{ai_reply_1}\n搜索引擎输出:{ai_reply_2}\n科研模型输出:{ai_reply_3}\n",
                    "knowledge_id": tmp_kb_id,
                    "temperature": 0.3,
                    "model_name": "chatglm3-6b",
                    "prompt_name": "agent_integration",
                    "history": conversation_history[-10:],
                    "max_tokens": 4096,
                    "top_k": 10,
                    "stream": True,
                }
            else:
                data_4 = {
                    "query": f"原生模型输出：{ai_reply_1}\n搜索引擎输出:{ai_reply_2}\n科研模型输出:{ai_reply_3}\n",
                    "knowledge_id": tmp_kb_id,
                    "temperature": 0.3,
                    "model_name": "chatglm3-6b",
                    "prompt_name": "agent_integration",
                    "max_tokens": 4096,
                    "top_k": 10,
                    "stream": True,
                }

            # 获取整合后的最终回答
            ai_reply = ""
            origin_docs = []


            async with aiohttp.ClientSession() as session:
                payload_5 = json.dumps(data_4)
                async with session.post(file_chat_url, data=payload_5, headers=headers) as response:
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith(': ping'):
                            continue
                        if decoded_line.startswith('data'):
                            data = json.loads(decoded_line.replace('data: ', ''))
                            if "answer" in data:
                                ai_reply += data["answer"]
                                yield {'type': 'answer', 'content': data["answer"], 'source': 'final'}
                            if "docs" in data:
                                for doc in data["docs"]:
                                    doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                                    origin_docs.append(doc)
                                    yield {'type': 'doc', 'content': doc, 'source': 'final'}

            # 获取推荐问题
            payload = json.dumps(
                {
                    "query": f"问题：{query}\n 回复：{ai_reply}",
                    "knowledge_id": tmp_kb_id,
                    "history": conversation_history[-4:],
                    "prompt_name": "literature_research_assistant",
                    "temperature": 0.4,
                    "stream": True,
                }
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(file_chat_url, data=payload, headers=headers) as response:
                    question_response = ""
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith(': ping'):
                            continue
                        if decoded_line.startswith('data'):
                            data = json.loads(decoded_line.replace('data: ', ''))
                            question_response += data.get("answer", "")

            question_reply = re.findall(r'"prediction_\d+":\s*"([^"]+)"', question_response)
            question_reply = question_reply[:2]
            question_reply.append("针对上一个问题做更详细的回复")

            # 最终返回推荐问题
            yield {'type': 'questions', 'content': question_reply}

        # 决定是否需要多模型处理
        need_2, need_3 = await need_distribution()

        if need_2 or need_3:
            # 多模型处理
            async for chunk in process_multi_models(need_2, need_3):
                yield chunk
        else:
            # 单模型处理
            async with aiohttp.ClientSession() as session:
                async with session.post(file_chat_url, data=payload, headers=headers) as response:
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith(': ping'):
                            continue
                        if decoded_line.startswith('data'):
                            data = json.loads(decoded_line.replace('data: ', ''))
                            if "answer" in data:
                                ai_reply += data["answer"]
                                yield {'type': 'answer', 'content': data["answer"], 'source': 'single'}
                            if "docs" in data:
                                for doc in data["docs"]:
                                    doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                                    origin_docs.append(doc)
                                    yield {'type': 'doc', 'content': doc, 'source': 'single'}

            # 获取推荐问题
            payload = json.dumps(
                {
                    "query": f"问题：{query}\n 回复：{ai_reply}",
                    "knowledge_id": tmp_kb_id,
                    "history": conversation_history[-4:],
                    "prompt_name": "literature_research_assistant",
                    "temperature": 0.4,
                    "stream": True,
                }
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(file_chat_url, data=payload, headers=headers) as response:
                    question_response = ""
                    async for line in response.content:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith(': ping'):
                            continue
                        if decoded_line.startswith('data'):
                            data = json.loads(decoded_line.replace('data: ', ''))
                            question_response += data.get("answer", "")

            question_reply = re.findall(r'"prediction_\d+":\s*"([^"]+)"', question_response)
            question_reply = question_reply[:2]
            question_reply.append("针对上一个问题做更详细的回复")

            # 最终返回推荐问题
            yield {'type': 'questions', 'content': question_reply, 'source': 'final'}

            yield {'type': 'end', 'content': "对话结束"}

    # 返回生成器
    return stream_generator()


def add_conversation_history(conversation_history, query, ai_reply, conversation_path):
    # 添加历史记录并保存
    conversation_history.extend(
        [
            {"role": "user", "content": query},
            {
                "role": "assistant",
                "content": ai_reply if ai_reply != "" else "此问题由于某原因无回答",
            },
        ]
    )

    with open(conversation_path, "w") as f:
        json.dump({"conversation": conversation_history}, f, indent=4)


"""
    论文研读 Key! 此时AI回复为非流式输出, 可能浪费时间, alpha版本先这样
"""

from business.utils.activity import update_user_activity
from django.http import StreamingHttpResponse
async def do_paper_study(request) -> StreamingHttpResponse:
    # 鉴权
    username = request.session.get("username")
    if username is None:
        username = "zjq"
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")
    update_user_activity(user.user_id, type='study')
    request_data = json.loads(request.body)
    query = request_data.get("query")  # 本次询问对话
    file_reading_id = request_data.get("file_reading_id")
    try:
        fr = FileReading.objects.get(id=file_reading_id)
    except FileReading.DoesNotExist:
        return reply.fail(msg="研读会话不存在")
    tmp_kb_id = get_tmp_kb_id(file_reading_id=file_reading_id)  # 临时知识库id
    if tmp_kb_id is None:
        return reply.fail(msg="请先创建研读会话")
    # 加载历史记录
    if not os.path.exists(fr.conversation_path):
        os.makedirs(os.path.dirname(fr.conversation_path), exist_ok=True)
        with open(fr.conversation_path, "w") as f:
            json.dump({"conversation": []}, f, indent=4)

    with open(fr.conversation_path, "r") as f:
        conversation_history = json.load(f)

    # print(tmp_kb_id)
    conversation_history = list(conversation_history.get("conversation"))
    print (f"time_start: {datetime.datetime.now()}")

    # 获取流式生成器
    stream_generator = await do_file_chat(conversation_history, query, tmp_kb_id)

    # 创建流式响应
    async def event_stream():
        async for chunk in stream_generator:
            if chunk['type'] == 'answer':
                yield json.dumps({
                    "type": "answer",
                    "content": chunk['content'],
                    "source": chunk.get('source', 'base_model'),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }) +"\n"
            elif chunk['type'] == 'doc':
                yield json.dumps({
                    "type": "doc",
                    "content": chunk['content'],
                    "source": chunk.get('source', 'base_model'),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }) + "\n"
            elif chunk['type'] == 'questions':
                yield json.dumps({
                    "type": "questions",
                    "content": chunk['content'],
                    "source": chunk.get('source', 'base_model'),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }) + "\n"
            elif chunk['type'] == 'end':
                yield json.dumps({
                    "type": "end",
                    "content": "对话结束",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }) + "\n"


        yield json.dumps({
            "type": "final_end",
            "content": "会话已完成",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }) + "\n"

    # 返回StreamingHttpResponse对象
    return StreamingHttpResponse( event_stream(), content_type='text/event-stream')


"""
    论文研读：重新生成回复

"""


@require_http_methods(["POST"])
def re_do_paper_study(request):
    # 鉴权
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")
    update_user_activity(user.user_id, type='study')
    request_data = json.loads(request.body)
    file_reading_id = request_data.get("file_reading_id")
    tmp_kb_id = get_tmp_kb_id(file_reading_id=file_reading_id)
    if tmp_kb_id is None:
        return reply.fail(msg="请先创建研读会话")
    try:
        fr = FileReading.objects.get(id=file_reading_id)
    except FileReading.DoesNotExist:
        return reply.fail(msg="研读会话不存在")
    conversation_path = fr.conversation_path
    with open(fr.conversation_path, "r") as f:
        conversation_history = json.load(f)

    conversation_history = list(conversation_history.get("conversation"))
    if len(conversation_history) < 2:
        return reply.fail(msg="无法找到您的上一条对话")
    # 获取最后一次的询问, 并去除最后一次的对话记录
    query = conversation_history[-2].get("content")
    conversation_history = conversation_history[:-2]

    # 同 do_paper_study
    ai_reply, origin_docs, question_reply = do_file_chat(
        conversation_history, query, tmp_kb_id
    )
    add_conversation_history(conversation_history, query, ai_reply, conversation_path)
    return reply.success(
        {"ai_reply": ai_reply, "docs": origin_docs, "prob_question": question_reply},
        msg="成功",
    )

@require_http_methods(["POST"])
def clear_conversation(request):
    # 鉴权
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    user = User.objects.filter(username=username).first()
    if user is None:
        return reply.fail(msg="请先正确登录")

    request_data = json.loads(request.body)
    file_reading_id = request_data.get("file_reading_id")
    fr = FileReading.objects.get(id=file_reading_id)
    os.makedirs(os.path.dirname(fr.conversation_path), exist_ok=True)
    with open(fr.conversation_path, "w") as f:

        json.dump({"conversation": []}, f, indent=4)
    return reply.success(msg="清除对话历史成功")