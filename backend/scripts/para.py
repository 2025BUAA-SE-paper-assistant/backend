# pip install PyMuPDF

import fitz

doc = fitz.open(
    '/Users/admin/Downloads/need_to_fix 2/pdf/e904a020-cdff-444a-b9a5-65e328c62fae.pdf'
)
for page_num in range(doc.page_count):
    page = doc[page_num]
    blocks = page.get_text("blocks")
    for i, block in enumerate(blocks):
        print(f"Paragraph {i+1}: {block}")
