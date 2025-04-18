import time
import psutil
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.before_request
def log_request_time():
    request.start_time = time.time()
    print(f"Received POST request at {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(request.start_time))}")

@app.after_request
def log_response_time(response):
    duration = time.time() - request.start_time
    print(f"Request processed in {duration:.4f} seconds")
    return response


@app.route('/get_server_info', methods=['POST'])
def get_server_info():
    return jsonify({
        "aaa": "cpu_info",
        "bbb": "memory_info",
        "ccc": "gpu_info",
        "message": "模型服务器硬件信息获取成功"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7863, threaded=True)
