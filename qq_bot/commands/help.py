# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #help指令 - 显示Bot帮助信息和指令列表
# 模型: mimo/mimo-v2.5

"""#help 指令 - 显示帮助信息"""
import logging
import re

from formatter.help import format_help

logger = logging.getLogger(__name__)


async def handle_help(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
    """
    处理 #help 指令
    返回帮助信息
    """
    logger.info("#help指令")
    return format_help()
