import sys
import logging

from loguru import logger

# 配置 loguru
logger.remove()  # 移除默认的处理器
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add("debug.txt", rotation="1 GB", level="DEBUG")
