'''用户活跃度相关的工具函数'''
from datetime import datetime, timedelta
from business.models.statistic import UserActivityStat
from business.models.user import User


def calculate_user_activity(user_id: str) -> int:
    """
    计算用户活跃度
    :param user_id: 用户ID
    :return: 活跃度值
    """
    # 获取当前时间
    now = datetime.now()
    # 计算过去7天的时间范围
    start_time = now - timedelta(days=7)

    # 查询过去7天内的用户活跃行为记录
    activities = UserActivityStat.objects.filter(user_id=user_id, timestamp__gte=start_time)

    # 计算活跃度值（例如：活动数量）
    activity_value = activities.count()

    return activity_value

