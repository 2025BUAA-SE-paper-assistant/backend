import fitz

# 打开 PDF 文件
doc = fitz.open("test.pdf")
page = doc[0]  # 获取第一页

# 提取文本块
blocks = page.get_text("blocks")
block = blocks[2]  # 选择第 1 个块
x0, y0, x1, y1, text, block_type, block_number = block

# 添加高亮批注
rect = [x0, y0, x1, y1]
highlight = page.add_highlight_annot(rect)
highlight.set_colors(stroke=(1, 1, 0))  # 黄色高亮
highlight.update()

# 动态检测空白位置
offset = 20
page_width = page.rect.width
page_height = page.rect.height

if x1 + offset < page_width:
    point = (x1, y0)  # 右侧
elif x0 - offset > 0:
    point = (x0 - offset, y0)  # 左侧
elif y0 - offset > 0:
    point = (x0, y0 - offset)  # 上方
else:
    point = (x0, y0)  # 默认

# 添加文本注释并设置图标
annot = page.add_text_annot(point, "这是一个段落级批注?")
annot.icon = "Comment"  # 直接设置 icon 属性
# annot.set_colors(stroke=(0, 0, 1))  # 蓝色边框
annot.set_opacity(0.8)
annot.update()

# 保存修改后的 PDF
doc.save("test_annotated.pdf")
doc.close()

'''
图标样式
"Note"（默认）：黄色便签图标。
"Comment"：类似对话气泡。
"Key"：钥匙图标。
"Help"：问号图标。
"NewParagraph"：段落符号。
"Paragraph"：段落标记。
"Insert"：插入符号。
"Circle"：圆形图标。
"Check"：勾选标记。
'''