"""
数据库统计
"""
from django.db import models


class UserDailyAddition(models.Model):
    """
    Field:
        - date          时间
        - addition      用户新增
    """
    date = models.DateField(auto_now=True)
    addition = models.IntegerField(default=0)


class UserVisit(models.Model):
    """
    Field:
        - ip_address    客户端 ip 地址
        - timestamp     访问时间
    """
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('ip_address', 'timestamp')




# 搜索关键词统计
class KeywordStat(models.Model):
    keyword = models.CharField(max_length=100)
    count = models.PositiveIntegerField(default=0)
    period = models.DateTimeField()  # 每个小时的起始时间

    class Meta:
        unique_together = [['keyword', 'period']]  # 确保同一小时内的关键词唯一
        indexes = [
            models.Index(fields=['period', 'keyword']),  # 优化查询速度
        ]

    def __str__(self):
        return f"{self.keyword} ({self.period}): {self.count}"


# 用户活跃行为统计
class UserActivityStat(models.Model):
    user_id = models.CharField(max_length=100)  # 用户ID
    activity_point  = models.IntegerField(default=0)  # 活跃权重
    timestamp = models.DateTimeField(auto_now_add=True)  # 活动发生的时间

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'timestamp']),  # 优化查询速度
        ]

    def __str__(self):
        return f"{self.user_id} - {self.activity_point} at {self.timestamp}"