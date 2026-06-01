# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #流派指令 - 返回所有可用流派列表
# 模型: mimo/mimo-v2.5

"""#流派 指令 - 查看所有流派"""
import logging
import re

from formatter.category import format_categories

logger = logging.getLogger(__name__)


async def handle_category(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
    """
    处理 #流派 指令
    返回所有流派列表
    """
    logger.info("#流派指令")
    return format_categories()
