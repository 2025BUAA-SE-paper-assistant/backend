'''用户活跃度相关的工具函数'''
from datetime import datetime, timedelta
from business.models.statistic import UserActivityStat
from business.models.user import User

acitivity_points = {
    'login': 7,  # 登录
    'search': 3,  # 搜索
    'upload': 10,  # 上传
    'download': 5,  # 下载
    'comment': 5,  # 评论
    'annotation': 5,  # 批注
    'study': 3,  # 研读
    'summarize': 3,  # 摘要总结 
    'like':1 #点赞
}
# TODO 更新批注相关
def update_user_activity(user_id, type='login'):
    """
    更新用户活跃度
    :param user_id: 用户id
    :param type: 活跃类型
    """
    if type not in acitivity_points:
        raise ValueError(f"Invalid activity type: {type}")

    # 获取当前时间
    now = datetime.now()
    # 获取用户的活跃度记录
    user_activity = UserActivityStat(user_id=user_id, 
                                     activity_point=acitivity_points[type],
                                     timestamp=now)
    # 更新活跃度
    user_activity.save()
