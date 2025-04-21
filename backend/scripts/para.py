# pip install PyMuPDF

import json
import fitz

doc = fitz.open(
    '/usr/zjq/backend/backend/resource/database/papers/0cac60c1-cb66-466f-906a-0bf3cd797378.pdf'
)
for page_num in range(doc.page_count):
    page = doc[page_num]
    blocks = page.get_text("blocks")
    for i, block in enumerate(blocks):
        block_list = list(block)
        paragraph_with_page = {
                    "page_num": page_num,
                    "block": block_list
                }
        print(json.dumps(paragraph_with_page))
