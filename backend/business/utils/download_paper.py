import json
import logging
import requests
from business.models.paper import Paper
from backend.settings import PAPERS_PATH
import os
import fitz  # 确保导入 PyMuPDF


if not os.path.exists(PAPERS_PATH):
    os.makedirs(PAPERS_PATH)


def downloadPaper(url, filename):
    """
    下载文献到服务器
    """
    # os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    # os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    path = os.path.join(PAPERS_PATH, filename) if filename.endswith('.pdf') else os.path.join(PAPERS_PATH, filename + '.pdf')
    if os.path.exists(path):
        return path
    command = f"wget {url} -O {path} "
    result = os.system(command)
    if result == 0:
        logging.info(f"下载成功: {url}")
        doc = fitz.open(
            path
        )
        paper = Paper.objects.get(paper_id = filename)
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

        return path
    else:
        logging.error('下载失败')
        return None
