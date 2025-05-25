import json
import logging
import openai
import re

def extract_and_clean_mermaid(content):
    # 提取三个反引号之间的内容，允许多行
    # 非贪婪匹配，直到遇到下一个```或字符串结尾
    pattern = r'```([\s\S]*?)(?:```|$)'
    match = re.search(pattern, content)

    if match:
        mermaid_content = match.group(1).strip()
        # 去除字符串中的"mermind"（假设是拼写错误，可能想删除"mermaid"）
        cleaned_content = mermaid_content.replace('mermaid', '')
        return cleaned_content
    else:
        logging.warning("No mermaid content found in the input string.")
        return content

class DeepSeek:
    def __init__(self, api_key="", base_url="https://api.deepseek.com/v1"):
        self.api_key = api_key if api_key else "sk-b0996543be5941d9a2bad73b9b12df35"
        self.base_url = base_url
        openai.api_key = self.api_key
        openai.api_base = self.base_url

    def chat(self, content):
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个深度学习助手，帮助用户解决问题"},
                {"role": "user", "content": content},
            ],
            max_tokens=1024,
            temperature=0.0,
            stream=False
        )
        print(response["choices"][0]["message"]["content"])
        return response["choices"][0]["message"]["content"]

    def read_md_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except FileNotFoundError:
            print(f"文件未找到: {file_path}")
            return None
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return None

    def translate_text(self, text):
        #TODO: 讲这里的硬编码改到配置里面
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.read_md_file("/usr/zjq/backend/backend/business/utils/translate.md")},
                {"role": "user", "content": json.dumps(text)},
            ],
            max_tokens=1024,
            temperature=0.0,
            stream=False
        )
        # print(response["choices"][0]["message"]["content"])
        return response["choices"][0]["message"]["content"]

        # return extract_and_clean_mermaid(mermind)

    def get_mind_map(self, text):
        #TODO: 讲这里的硬编码改到配置里面
        response = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": self.read_md_file("/usr/zjq/backend/backend/business/utils/mind_map.md")},
                {"role": "user", "content": json.dumps(text)},
            ],
            max_tokens=1024,
            temperature=0.0,
            stream=False
        )
        # print(response["choices"][0]["message"]["content"])
        mermaid = response["choices"][0]["message"]["content"]
        return extract_and_clean_mermaid(mermaid)

if __name__ == "__main__":
    ds = DeepSeek(api_key="sk-b0996543be5941d9a2bad73b9b12df35")
    # ds.chat("讲一个冷笑话")
    file_content = ds.translate_text('''  We propose a novel method to generate fabrication blueprints from images of
carpentered items. While 3D reconstruction from images is a well-studied
problem, typical approaches produce representations that are ill-suited for
computer-aided design and fabrication applications. Our key insight is that
fabrication processes define and constrain the design space for carpentered
objects, and can be leveraged to develop novel reconstruction methods. Our
method makes use of domain-specific constraints to recover not just valid
geometry, but a semantically valid assembly of parts, using a combination of
image-based and geometric optimization techniques.
  We demonstrate our method on a variety of wooden objects and furniture, and
show that we can automatically obtain designs that are both easy to edit and
accurate recreations of the ground truth. We further illustrate how our method
can be used to fabricate a physical replica of the captured object as well as a
customized version, which can be produced by directly editing the reconstructed
model in CAD software.
''')
    # print(file_content)