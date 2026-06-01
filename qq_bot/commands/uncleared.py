# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #未通关指令 - 按活动名和流派查询未通关关卡
# 模型: mimo/mimo-v2.5

"""#未通关 指令 - 查未通关关卡"""
import logging
import re

from api_client import WikiClient
from resolver.category import normalize_category
from formatter.uncleared import format_uncleared
from config import config

logger = logging.getLogger(__name__)


async def handle_uncleared(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
    """
    处理 #未通关 指令
    格式: #未通关 <活动名> <流派>
    示例: #未通关 惊霆无声 四星队
    """
    args = match.group(1).strip()
    
    # 解析参数
    parts = args.split()
    if len(parts) < 2:
        return (
            "缺少流派参数，格式：#未通关 <活动名> <流派>\n"
            "发送 #流派 查看所有流派"
        )
    
    episode = parts[0]
    category_input = parts[1]
    
    # 归一流派名
    category = normalize_category(category_input)
    if not category:
        return f"未找到流派 \"{category_input}\"，发送 #流派 查看所有流派"
    
    logger.info(f"#未通关指令: episode={episode}, category={category}")
    
    try:
        # 调用wiki API查询未通关关卡
        async with WikiClient(base_url=config.wiki_base_url, token=config.wiki_api_token) as client:
            result = await client.uncleared(episode=episode, category=category)
            
            # 格式化返回结果（传入 operation_index 以显示难度标签）
            return format_uncleared(result.episode, result.category, result.uncleared, operation_index)
    except Exception as e:
        logger.error(f"查询未通关关卡失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"
