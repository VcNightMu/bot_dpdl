# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #未通关指令 - 按活动名和流派查询未通关关卡
# 模型: mimo/mimo-v2.5

"""#未通关 指令 - 查未通关关卡

突袭等效普通规则：has_challenge=True 的关卡，如果只有 normal
未通关但没有 challenge 未通关，说明突袭已通过，普通视为已通关，不展示。
"""
import logging
import re

from api_client import WikiClient
from resolver.category import normalize_category
from formatter.uncleared import format_uncleared
from config import config

logger = logging.getLogger(__name__)


def filter_uncleared(
    uncleared: list[dict],
    operation_index: dict | None = None,
) -> list[dict]:
    """过滤未通关列表，处理突袭等效普通。

    has_challenge=True 的关卡：
    - 只有 normal 未通关 → 去掉（突袭已通过）
    - 只有 challenge 或两个都有 → 保留
    """
    if not operation_index:
        return uncleared

    # 按 operation 分组
    by_op: dict[str, list[dict]] = {}
    for item in uncleared:
        op = item.get("operation", "???").upper()
        by_op.setdefault(op, []).append(item)

    # 收集需要剔除的 (operation, difficulty) 对
    remove: set[tuple[str, str]] = set()
    for op, items in by_op.items():
        info = operation_index.get("by_operation", {}).get(op)
        if not info or not info.get("has_challenge", False):
            continue

        difficulties = {item.get("difficulty", "normal") for item in items}
        # 只有 normal 没有 challenge → 去掉 normal
        if difficulties == {"normal"}:
            remove.add((op, "normal"))

    if not remove:
        return uncleared

    logger.info(f"突袭等效普通，剔除: {remove}")
    return [
        item for item in uncleared
        if (item.get("operation", "???").upper(), item.get("difficulty", "normal")) not in remove
    ]


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
            
            # 过滤：突袭等效普通（只收到normal时去掉）
            uncleared = filter_uncleared(result.uncleared, operation_index)
            
            # 格式化返回结果（传入 operation_index 以显示难度标签）
            return format_uncleared(result.episode, result.category, uncleared, operation_index)
    except Exception as e:
        logger.error(f"查询未通关关卡失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"
