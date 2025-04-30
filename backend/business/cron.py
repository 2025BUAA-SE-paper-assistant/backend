'''定时任务'''
from business.utils.recommend import refresh_personal_recommend_cache
from business.models import User
from business.models.statistic import UserActivityStat
from django.utils import timezone
from datetime import timedelta
import logging
logger = logging.getLogger('business')
def refresh_all_personal_recommend_cache():
    '''个性化推荐缓存定时任务'''
    # users = User.objects.all()
    # 仅为过去三天的活跃用户设置缓存
    end_time = timezone.now()
    start_time = end_time - timedelta(days=3)
    user_ids = list(UserActivityStat.objects.filter(
        timestamp__range=(start_time, end_time)
    ).values_list('user_id', flat=True).distinct())
    users = User.objects.filter(user_id__in=user_ids).all()
    max_retries = 3  # 最大重试次数
    for user in users:
        for attempt in range(max_retries):
            try:
                refresh_personal_recommend_cache(user)
                logger.info(f"Successfully set cache for user {user.user_id}")
                break  # 如果成功，跳出重试循环
            except Exception as e:
                logger.error(f"Error setting cache for user {user.user_id}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to set cache for user {user.user_id} after {max_retries} attempts.")

