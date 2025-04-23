'''定时任务'''
from business.utils.recommend import refresh_personal_recommend_cache
from business.models import User
import logging

def refresh_all_personal_recommend_cache():
    '''个性化推荐缓存定时任务'''
    users = User.objects.all()
    max_retries = 3  # 最大重试次数
    for user in users:
        for attempt in range(max_retries):
            try:
                refresh_personal_recommend_cache(user)
                logging.info(f"Successfully set cache for user {user.user_id}")
                break  # 如果成功，跳出重试循环
            except Exception as e:
                logging.error(f"Error setting cache for user {user.user_id}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to set cache for user {user.user_id} after {max_retries} attempts.")

