import requests
import json
import gzip
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置Session和重试策略
session = requests.Session()
retries = Retry(
    total=5,  # 重试次数
    backoff_factor=0.3,  # 退避因子
    status_forcelist=[500, 502, 503, 504],  # 需要重试的状态码
)
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)

# 读取数据
with open("/usr/zjq/payload_output.json", 'r') as file:
    data = json.load(file)
texts = data.get("texts", [])

# 压缩payload
payload = json.dumps({"texts": texts})
compressed_payload = gzip.compress(payload.encode('utf-8'))

# 设置URL和请求头
url = "http://10.2.16.28:2334/other/embed_texts"
headers = {
    "Content-Type": "application/json",
    "Content-Encoding": "gzip"  # 告知服务器数据已压缩
}

try:
    # 发送请求
    response = session.post(
        url,
        headers=headers,
        data=compressed_payload,
        timeout=(600000, 600000)  # 30秒连接超时，60秒读取超时
    )
    response.raise_for_status()  # 检查状态码
    with open("/home/am3/output.txt", "w", encoding="utf-8") as f:
        f.write(response.text)
except requests.exceptions.ConnectTimeout:
    print("连接服务器超时。")
except requests.exceptions.ReadTimeout:
    print("服务器响应时间过长。")
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误 {response.status_code}: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
finally:
    session.close()  # 关闭会话