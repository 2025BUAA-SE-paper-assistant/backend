import requests

# JSON文件路径
json_file_path = "/Users/admin/PycharmProjects/backend/payload_output copy.json"

# 服务端URL
url = "http://10.2.16.28:2336/upload"

# 打开文件并发送POST请求
with open(json_file_path, "rb") as file:
    files = {"files": (json_file_path, file, "application/json")}
    response = requests.post(url, files=files, timeout=(60000, 60000))

# 打印响应
print(response.status_code)
print(response.text)
