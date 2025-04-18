import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置Session和重试策略
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 读取数据
with open("E:\\code\\ruangong\\backend\\payload_output.json", "r") as file:
    data = json.load(file)
texts = data.get("texts", [])
payload = json.dumps({"texts": texts})
headers = {"Content-Type": "application/json"}

url = "http://10.2.16.28:2334/other/embed_texts"

try:
    response = session.post(
        url,
        headers=headers,
        data=payload,
        timeout=(30, 120),  # 连接超时30秒，读取超时120秒
    )
    response.raise_for_status()
    print("Response:", response.text)
except requests.exceptions.ConnectTimeout:
    print("Connection to server timed out.")
except requests.exceptions.ReadTimeout:
    print("Server took too long to respond.")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error {response.status_code}: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
finally:
    session.close()
