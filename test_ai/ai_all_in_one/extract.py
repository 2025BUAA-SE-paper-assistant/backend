import json
import random
import pandas as pd

# 读取json文件
with open('/usr/zjq/backend/backend/scripts/paper.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 将数据转换为DataFrame以便操作
df = pd.DataFrame(data)

# 确保至少有20条记录可以抽取，否则调整抽样数量
sample_size = min(20, len(df))

# 随机抽取样本
sampled_data = df.sample(n=sample_size)

history = ""

# 打印每篇论文的标题和摘要
i = 0
for index, row in sampled_data.iterrows():
    # print("Title:", row['title'])
    # print("Abstract:", row['abstract'])
    # print("-" * 50)  # 分隔线
    i = i + 1
    history += f"Title_{i}: {row['title']}\n"

print(history)