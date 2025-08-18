# API文档：https://help.aliyun.com/document_detail/434034.html

# 调用方法：https://help.aliyun.com/document_detail/433945.html

# 计费方式：https://help.aliyun.com/document_detail/464388.html（1小时1结算）

# 代码：

# ```python
# pip install alibabacloud_green20220302==2.2.8
# coding=utf-8

from alibabacloud_green20220302.client import Client
from alibabacloud_green20220302 import models
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_tea_util import models as util_models
import json
import uuid
from loguru import logger

class GreenCheck:

    def __init__(self):
        self.config = Config(
            access_key_id='',
            access_key_secret='',
            # 连接时超时时间，单位毫秒（ms）。
            connect_timeout=3000,
            # 读取时超时时间，单位毫秒（ms）。
            read_timeout=6000,
            # 接入区域和地址请根据实际情况修改。
            region_id='cn-beijing',
            endpoint='green-cip.cn-beijing.aliyuncs.com'
        )
        self.client = Client(self.config)

    def check(self,content) -> None:
        service_parameters = {"content": content, "dataId": str(uuid.uuid1())}
        text_moderation_request = models.TextModerationRequest(
            service="comment_detection",
            service_parameters=json.dumps(service_parameters),
        )
        runtime = util_models.RuntimeOptions()
        runtime.read_timeout = 10000
        runtime.connect_timeout = 10000
        try:
            response = self.client.text_moderation_with_options(text_moderation_request, runtime)
            # 自动路由
            if UtilClient.equal_number(500, response.status_code) or not response or not response.body or 200 != response.body.code:
                # 服务端错误，区域切换到cn-beijing
                self.config.region_id = 'cn-beijing'
                self.config.endpoint = 'green-cip.cn-beijing.aliyuncs.com'
                self.client = Client(self.config)
                response = self.client.text_moderation_with_options(text_moderation_request, runtime)

            if response.status_code == 200:
                # 调用成功。
                # 获取审核结果。
                result = response.body
                logger.info('response success. result:{}'.format(result))

                if result.code == 200 and not result.data.labels:
                    # labels为空，表示没有检测到敏感内容。
                    return True, "success"
                else:
                    description = result.data.descriptions
                    resultData = result.data
                    logger.info('resultData:{}'.format(resultData))
                    return False, description
            else:
                description = result.data.descriptions
                logger.warning('response not success. status:{} ,result:{}'.format(response.status_code, response.body))
                # print(description)
                return False, description
        except Exception as err:
            logger.error(err)
            return False, f"{err}"

if __name__ == '__main__':
    green_check = GreenCheck()
    content = "毛泽东"
    print(green_check.check(content))

