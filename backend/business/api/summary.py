"""
本文件主要用于文献综述生成，包括单篇文献的综述生成和多篇文献的综述生成
path : /api/summary/...
"""

from django.http import JsonResponse, HttpRequest
import openai, json
from business.models import User, paper, Notification
import threading, requests
from business.utils.reply import fail, success
from django.conf import settings
from business.models import User, UserDocument, Paper, abstract_report, SummaryReport
from django.views.decorators.http import require_http_methods
import os,re


##################################新建一个临时知识库，多问几次，然后通过一个模板生成综述#######################################

###################综述生成##########################

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def queryGLM(msg: str, history=None) -> str:
    """
    对chatGLM3-6B发出一次单纯的询问
    """
    # print(msg)
    chat_chat_url = "http://10.2.16.28:2334/chat/chat"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps({"query": msg, "prompt_name": "default", "temperature": 0.3})

    session = requests.Session()
    retry = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.post(
            chat_chat_url, data=payload, headers=headers, stream=False
        )
        response.raise_for_status()

        # 确保正确处理分块响应

        data = None
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
                continue
            print(decoded_line)
            if decoded_line.startswith('data'):
                data = json.loads(decoded_line.replace('data:', ''))
        if isinstance(data, dict) and 'text' in data:
            return data['text']
        return "错误: 无法获取响应"
    except requests.exceptions.ChunkedEncodingError as e:
        print(f"ChunkedEncodingError: {e}")
        return "错误: 响应提前结束"
    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")
        return f"错误: {e}"

import re

def convert_markdown(md_content):
    # 去除标题和列表项前的多余空格
    md_content = re.sub(r'^\s+(#+ .+)$', r'\1', md_content, flags=re.MULTILINE)
    md_content = re.sub(r'^\s+(\d+\. .+)$', r'\1', md_content, flags=re.MULTILINE)
    
    # 在标题后添加空行（确保标题后有空行）
    md_content = re.sub(r'(#+ .+)\n(?!\n|#)', r'\1\n\n', md_content, flags=re.MULTILINE)
    
    # 调整子项缩进（3空格 -> 4空格）
    md_content = re.sub(r'^   -', r'    -', md_content, flags=re.MULTILINE)
    return md_content  # Make sure to return the processed content

from weasyprint import HTML
import markdown
from jinja2 import Template

def markdown_to_pdf(input_md, output_pdf):
    with open(input_md, 'r', encoding='utf-8') as f:
        md_text = f.read()

        if not md_text:
            raise ValueError("Markdown file is empty")

    md_text = convert_markdown(md_text)

    html_content = markdown.markdown(md_text, extensions=['extra','tables', 'sane_lists'])
    template_path = os.path.join(settings.USER_REPORTS_PATH, "template.html")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found at {template_path}")

    with open(template_path, 'r', encoding='utf-8') as t:
        template = Template(t.read())
    full_html = template.render(content=html_content)


    HTML(string=full_html).write_pdf(output_pdf)

def get_summary(paper_ids, report_id, user):
    print("report_id:", report_id)
    report = SummaryReport.objects.get(report_id=report_id)
    report.status = SummaryReport.STATUS_IN_PROGRESS
    ret_content = "你关于论文"
    try:
        paper_content = []  # 每个论文一个标题，然后是内容
        paper_conclusions = []
        paper_themes = []
        paper_situations = []
        ######生成标题########
        i = 1
        articles = ""
        for id in paper_ids:
            p = Paper.objects.filter(paper_id=id).first()
            articles += f"Title_{i}: {p.title}\nAbstrastract_{i}: {p.abstract}"
            ret_content += f"《{p.title}》、"
            i = i + 1
        ret_content = ret_content[:-2]
        base_url = "http://10.2.16.28:2334/chat" #ai URL
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            "query": f"{articles}", # 原文
            "temperature": 0.3, # temp
            "stream": False, 
            "model_name": "chatglm3-6b", # 模型
            "prompt_name": "literature_reviewer_plus", # prompt类型
        }

        payload = json.dumps(data)

        response = requests.post(f"{base_url}/chat", data=payload, headers=headers, stream=False)
        ans = ""
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
                continue
            if decoded_line.startswith('data'):
                data = json.loads(decoded_line.replace('data: ', ''))
                ans += data['text']

        pattern = r"标题：(.+?)(?:\r?\n|$)"

        titles = re.findall(pattern, ans) #生成综述标题
        title = titles[0]
            
        for id in paper_ids:
            p = Paper.objects.filter(paper_id=id).first()
            content_prompt = (
                "将这篇论文的摘要以第三人称的方式复述一遍，摘要如下：\n" + p.abstract_cn
            )
            paper_content.append(queryGLM(content_prompt, []))
            content_prompt = "将这篇论文的题目转化为中文：\n" + p.title
            paper_themes.append(queryGLM(content_prompt, []))
            # paper_themes.append(p.title_cn)
            content_prompt = (
                "将这篇论文的现状部分以第三人称的方式复述一遍：\n" + p.abstract_cn
            )
            paper_situations.append(queryGLM(content_prompt, []))
            content_prompt = (
                "将这篇论文的结论和展望部分以第三人称的方式复述一遍：\n" + p.abstract_cn
            )
            paper_conclusions.append(queryGLM(content_prompt, []))
        # 生成引言
        introduction_prompt = "请根据以下信息生成综述的引言：\n"
        for i in range(len(paper_ids)):
            introduction_prompt += (
                "第" + str(i + 1) + "篇论文的题目是：" + paper_themes[i] + "\n"
            )
            introduction_prompt += (
                "第" + str(i + 1) + "篇论文的现状部分是：" + paper_situations[i] + "\n"
            )
        introduction = queryGLM(introduction_prompt, [])
        # 生成结论
        conclusion_prompt = "请根据以下信息生成综述的结论：\n"
        for i in range(len(paper_ids)):
            conclusion_prompt += (
                "第" + str(i + 1) + "篇论文的题目是：" + paper_themes[i] + "\n"
            )
            conclusion_prompt += (
                "第" + str(i + 1) + "篇论文的结论部分是：" + paper_conclusions[i] + "\n"
            )
        conclusion = queryGLM(conclusion_prompt, [])

        print("结论生成完毕")
        print("关键技术分析开始")
        
        ###关键技术与创新点
        data = {
            "query": f"{articles}", # 原文
            "temperature": 0.2, # temp
            "stream": False, 
            "model_name": "chatglm3-6b", # 模型
            "max_tokens": 4096,
            "prompt_name": "tech_innovation_analyzer", # prompt类型
        }

        payload = json.dumps(data)

        response = requests.post(f"{base_url}/chat", data=payload, headers=headers, stream=False)
        ans = ""
        # 捕获输出
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
                continue
            if decoded_line.startswith('data'):
                data = json.loads(decoded_line.replace('data: ', ''))
                ans += data['text']

        lines = ans.splitlines()
        innovation = ""
        for idx, line in enumerate(lines):
            if line.strip() == '关键技术和创新突破':
                innovation += '\n'
                # 从匹配行开始，拼接后续所有行
                innovation = '\n'.join(lines[idx:]).strip() 
        # print("关键技术分析开始结束", ans)
        print("关键技术分析开始结束")
        
        #####局限性分析
        print("局限性分析开始")
        data = {
            "query": f"{articles}", # 原文
            "temperature": 0.3, # temp
            "stream": False, 
            "model_name": "chatglm3-6b", # 模型
            "max_tokens": 4096,
            "prompt_name": "performance_analyzer", # prompt类型
        }

        payload = json.dumps(data)

        response = requests.post(f"{base_url}/chat", data=payload, headers=headers, stream=False)
        ans = ""
        # 捕获输出
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith(': ping'):  # 忽略以 ":" 开头的行
                continue
            if decoded_line.startswith('data'):
                data = json.loads(decoded_line.replace('data: ', ''))
                ans += data['text']
        print("局限性分析结束")
        # print("局限性分析结束", ans)
        lines = ans.splitlines()
        # lines = [line for line in lines and line != '']
        limit = ""
        for idx, line in enumerate(lines):
            if line.strip() == '性能表现与领域局限':
                # 从匹配行开始，拼接后续所有行
                limit = '\n'.join(lines[idx:]).strip()

        # limit = "## " + limit     
                
                 
        # 生成综述
        summary = f"# {title}\n" + introduction + "\n"
        summary += "# 各论文内容简述\n"
        for i in range(len(paper_ids)):
            summary += "## " + paper_themes[i] + "\n"
            summary += paper_content[i] + "\n"
        if innovation != "" :
            innovation = "## " + innovation
            summary += innovation + "\n"
        if limit != "" :
            limit = "## " + limit
            summary += limit + "\n"
        summary += "\n# 结论\n" + conclusion + "\n"
        # 修改语病，更加通顺
        response = summary
        os.makedirs(os.path.dirname(settings.USER_REPORTS_PATH), exist_ok=True)
        md_path = settings.USER_REPORTS_PATH + "/" + str(report.report_id) + ".md"
        pdf_path = settings.USER_REPORTS_PATH + "/" + str(report.report_id) + ".pdf"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(response)
        markdown_to_pdf(md_path, pdf_path)
        report.report_path = pdf_path
        report.status = SummaryReport.STATUS_COMPLETED
        report.save()
        ret_content += "的综述报告生成完毕了！请前往“个人中心->综述报告”查看！"
        notification = Notification(user_id = user,title='综述报告生成成功！',content=ret_content)
        notification.save()
        # os.remove(md_path)
        # print(response)
    except Exception as e:                     # 发生异常所在的行数
        ret_content = "抱歉！" + ret_content + "的综述报告失败，请重新尝试。" 
        notification = Notification(user_id = user,title='综述报告生成失败！',content=ret_content)
        notification.save()
        report.delete()


@require_http_methods(["GET"])
def get_summary_status(request):
    """
    查询综述生成状态
    """
    report_id = request.GET.get("report_id")
    report = SummaryReport.objects.filter(report_id=report_id).first()
    if report is None:
        return fail(data={"status": "综述不存在"})
    if (
        report.status == SummaryReport.STATUS_PENDING
        or report.status == SummaryReport.STATUS_IN_PROGRESS
    ):
        return fail(data={"status": "正在生成中"})
    return success({"status": "生成成功"})


from business.utils.activity import update_user_activity
@require_http_methods(['POST'])
def generate_summary(request):
    """
    生成综述
    """
    data = json.loads(request.body)
    paper_ids = data.get("paper_id_list")
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    from business.models import SummaryReport, User

    user = User.objects.filter(username=username).first()

    if user is None:
        return fail(msg="请先正确登录")
    update_user_activity(user.user_id, type='summarize')
    report = SummaryReport.objects.create(user_id=user, status=SummaryReport.STATUS_PENDING)
    report.title = '综述' + str(report.report_id)
    # p = settings.USER_REPORTS_PATH + '/' + str(report.report_id) + '.md'
    p = settings.USER_REPORTS_PATH + '/' + str(report.report_id) + '.pdf'
    report.report_path = p
    report.save()
    try:
        print(report.report_id)
        # download_dir = settings.CACHE_PATH + '/' + str(report.report_id)
        # os.makedirs(download_dir)
        # # 先下载文章
        # for paper_id in paper_ids:
        #     download_paper(paper_id, download_dir)
        # # 创建临时知识库
        # tmp_kb_id = create_tmp_knowledge_base(download_dir)
        # if tmp_kb_id is None:
        #     return fail('创建临时知识库失败')
        # 开始生成综述
        # keywords = ['现状', '问题', '方法', '结果', '结论', '展望']
        if len(paper_ids) > 8:
            return fail(msg="综述生成输入文章数目过多")
        # 先把每篇论文需要的信息生成好了
        threading.Thread(target=get_summary, args=(paper_ids, report.report_id, user)).start()
        return JsonResponse(
            {"message": "综述生成成功", "report_id": report.report_id}, status=200
        )
    except Exception as e:
        print(e)
        report.delete()
        return JsonResponse({"message": "综述生成失败"}, status=400)


##################################单篇摘要生成##############################

import os
import requests
# from business.utils.download_paper import downloadPaper


def create_tmp_knowledge_base(dir: str) -> str:
    """
    将cache中的所有文件全部上传到远端服务器，创建一个临时知识库
    """
    # 上传到远端服务器, 创建新的临时知识库
    upload_temp_docs_url = (
        f"http://{settings.REMOTE_MODEL_BASE_PATH}/knowledge_base/upload_temp_docs"
    )
    payload = {}

    files = []
    import os

    # 遍历每个文件
    for root, dirs, files in os.walk(dir):
        for file in files:
            file_path = os.path.join(root, file)
            files.append(
                (
                    "files",
                    (
                        file,
                        open(file_path, "rb"),
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    ),
                )
            )
    response = requests.request("POST", upload_temp_docs_url, files=files)
    # print(response)
    # 关闭文件，防止内存泄露
    for k, v in files:
        v[1].close()

    if response.status_code == 200:
        tmp_kb_id = response.json()["data"]["id"]
        return tmp_kb_id
    else:
        return None


def ask_ai_single_paper(payload):
    file_chat_url = f"http://{settings.REMOTE_MODEL_BASE_PATH}/chat/file_chat"
    headers = {"Content-Type": "application/json"}
    response = requests.request(
        "POST", file_chat_url, data=payload, headers=headers, stream=False
    )
    ai_reply = ""
    origin_docs = []
    # print(response)
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
                if "docs" in data:
                    for doc in data["docs"]:
                        doc = str(doc).replace("\n", " ").replace("<span style='color:red'>", "").replace("</span>", "")
                        origin_docs.append(doc)
    return ai_reply, origin_docs

from business.api.paper_interpret import get_paper_local_url
from business.utils.activity import update_user_activity
def create_abstract_report(request):
    request_data = json.loads(request.body)
    document_id = request_data.get("document_id")
    paper_id = request_data.get("paper_id")
    username = request.session.get("username")
    if username is None:
        username = "sanyuba"
    print(username)
    user = User.objects.filter(username=username).first()
    if user is None:
        return fail(msg="请先正确登录")
    if document_id:
        document = UserDocument.objects.get(document_id=document_id)
        # 获取服务器本地的path
        local_path = document.local_path
        content_type = document.format
        title = document.title
    elif paper_id:
        p = Paper.objects.filter(paper_id=paper_id).first()
        local_path = get_paper_local_url(p)
        # pdf_url = p.original_url.replace("abs/", "pdf/") + ".pdf"
        # local_path = settings.PAPERS_URL + '/' + str(p.paper_id) + ".pdf"
        # print(local_path)
        # print(pdf_url)
        # if not os.path.exists(local_path):
        #     # 下载下来
        #     downloadPaper(url=pdf_url, filename=str(p.paper_id))
        content_type = ".pdf"
        title = str(p.paper_id)
    print("下载完毕")

    from business.models.abstract_report import AbstractReport

    report_path = os.path.join(settings.USER_REPORTS_PATH, str(title) + ".md")
    print(report_path)

    # 先查询存不存在响应的解读

    ar = AbstractReport.objects.filter(file_local_path=local_path).first()

    # 不存在
    if ar is None:
        # 创建一个线程，直接开始创建
        ## 先创建一个知识库
        ar = AbstractReport.objects.create(
            file_local_path=local_path, report_path=report_path
        )
        upload_temp_docs_url = (
            f"http://{settings.REMOTE_MODEL_BASE_PATH}/knowledge_base/upload_temp_docs"
        )
        # local_path = local_path[1:] if local_path.startswith("/") else local_path
        print(local_path)
        files = [
            (
                "files",
                (
                    str(title) + content_type,
                    open(local_path, "rb"),
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                ),
            )
        ]
        response = requests.post(upload_temp_docs_url, files=files)

        # 关闭文件，防止内存泄露
        for k, v in files:
            v[1].close()
        if response.status_code != 200:
            return fail(msg="连接模型服务器失败")
        tmp_kb_id = response.json()["data"]["id"]
        print(tmp_kb_id, report_path, local_path)
        abs_control_thread(
            tmp_kb_id=tmp_kb_id, report_path=report_path, local_path=local_path
        ).start()
        return success(msg="正在生成中，请稍后查看")
    elif (
        ar is not None
        and ar.status == AbstractReport.STATUS_PENDING
        or ar.status == AbstractReport.STATUS_IN_PROGRESS
    ):
        # 存在
        return success(msg="正在生成中，请稍后查看")
    elif ar is not None and ar.status == AbstractReport.STATUS_COMPLETED:
        # 存在
        return success(
            {"summary": open(ar.report_path, "r").read()}, msg="生成摘要成功"
        )
    else:
        assert ar.status == AbstractReport.STATUS_TIMEOUT
        ar.delete()
        return fail(msg="生成摘要失败")


from business.models.abstract_report import AbstractReport


class abs_control_thread(threading.Thread):
    def __init__(self, tmp_kb_id, report_path, local_path):
        threading.Thread.__init__(self)
        self.tmp_kb_id = tmp_kb_id
        self.report_path = report_path
        self.local_path = local_path
        self.ttl = 300  # 5分钟
        self.setDaemon(True)

    def run(self):
        import time

        cur = 0
        # 执行gen_abstract的时间不能超过ttl
        a = abs_gen_thread(self.tmp_kb_id, self.report_path, self.local_path)
        a.start()
        while cur < self.ttl:
            ar = AbstractReport.objects.get(file_local_path=self.local_path)
            if ar.status == AbstractReport.STATUS_COMPLETED:
                return
            cur += 1
            time.sleep(1)
        a.stop()


class abs_gen_thread(threading.Thread):
    def __init__(self, tmp_kb_id, report_path, local_path):
        threading.Thread.__init__(self)
        self.tmp_kb_id = tmp_kb_id
        self.report_path = report_path
        self.local_path = local_path
        self.isend = False
        self.setDaemon(True)

    def run(self):
        ar = AbstractReport.objects.get(file_local_path=self.local_path)
        ar.status = AbstractReport.STATUS_IN_PROGRESS
        summary = ""
        # 开始生成摘要
        ## 现状，解决问题，解决方法，实验结果，结论
        summary += "# 摘要报告\n"

        from business.api.paper_interpret import do_file_chat

        #### 研究现状
        if self.isend:
            ar.status = AbstractReport.STATUS_TIMEOUT
            return

        query_current_situation = "请讲述研究现状部分\n"
        payload_cur_situation = json.dumps(
            {
                "query": query_current_situation,
                "knowledge_id": self.tmp_kb_id,
                "prompt_name": "default",  # 使用普通对话模式
            }
        )
        response_current_situation, _ = ask_ai_single_paper(
            payload=payload_cur_situation
        )
        print(_)
        summary += "## 研究现状\n" + response_current_situation + "\n"
        if self.isend:
            ar.status = AbstractReport.STATUS_TIMEOUT
            return

        #### 解决问题

        query_problem = "请讲讲这篇论文解决的问题\n"
        payload_problem = json.dumps(
            {
                "query": query_problem,
                "knowledge_id": self.tmp_kb_id,
                "prompt_name": "default",
            }
        )
        response_problem, _ = ask_ai_single_paper(payload=payload_problem)
        print(_)
        summary += "## 解决问题\n" + response_problem + "\n"
        if self.isend:
            ar.status = AbstractReport.STATUS_TIMEOUT
            return
        #### 解决方法

        query_solution = "请讲讲这篇论文提出的解决方法\n"
        payload_solution = json.dumps(
            {
                "query": query_problem,
                "knowledge_id": self.tmp_kb_id,
                "prompt_name": "default",  # 使用普通对话模式
            }
        )
        response_solution, _ = ask_ai_single_paper(payload=payload_solution)
        print(_)
        summary += "## 解决方法\n" + response_solution + "\n"
        if self.isend:
            ar.status = AbstractReport.STATUS_TIMEOUT
            return
            #### 实验结果

        query_result = "请讲讲这篇论文实验得到的结果\n"
        payload_res = json.dumps(
            {
                "query": query_result,
                "knowledge_id": self.tmp_kb_id,
                "prompt_name": "default",  # 使用普通对话模式
            }
        )
        response_result, _ = ask_ai_single_paper(payload=payload_res)
        print(_)
        summary += "## 实验结果\n" + response_result + "\n"
        if self.isend:
            ar.status = AbstractReport.STATUS_TIMEOUT
            return
        #### 结论

        query_conclusion = "请讲讲这篇论文得出的结论\n"
        payload_conclusion = json.dumps(
            {
                "query": query_conclusion,
                "knowledge_id": self.tmp_kb_id,
                "prompt_name": "default",  # 使用普通对话模式
            }
        )
        response_conclusion, _ = ask_ai_single_paper(payload=payload_conclusion)
        print(_)
        summary += "## 结论\n" + response_conclusion + "\n"

        # 修改语病，更加通顺
        # print(summary)
        response = summary
        # print(response)
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(response)
        ar.report_path = self.report_path
        ar.status = AbstractReport.STATUS_COMPLETED
        ar.save()

    def stop(self):
        # 设置线程停止
        self.isend = True
