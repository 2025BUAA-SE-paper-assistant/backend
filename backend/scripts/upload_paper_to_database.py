import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

from business.models.paper import Paper
import json
from datetime import datetime
from django.http import JsonResponse

def refresh():
    Paper.objects.all().delete()

def refresh_paper(request):
    """
    从 JSON 文件中读取论文数据并存储到数据库中
    """
    refresh()
    with open('/usr/zjq/backend/backend/scripts/paper.json', 'r', encoding='utf-8') as f:
        papers = json.load(f)
        for paper in papers:
            # 将字符串日期转换为 datetime 对象
            publication_date = datetime.strptime(paper['publication_date'], '%Y-%m-%dT%H:%M:%SZ').date()
            Paper.objects.create(
                title=paper['title'],
                authors=paper['authors'],
                abstract=paper['abstract'],
                publication_date=publication_date,
                journal=None,  # 期刊允许为空，arXiv没有
                citation_count=paper['citation_count'],
                original_url=paper['original_url'],
                read_count=random.randint(0, 1000),
                like_count=0,
                collect_count=0,
                comment_count=0,
                download_count=random.randint(0, 1000)
            )
    return JsonResponse({"status": "success", "message": "论文数据已成功上传到数据库"})
