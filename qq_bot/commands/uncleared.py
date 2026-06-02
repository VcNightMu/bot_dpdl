# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #未通关指令 - 按活动名和流派查询未通关关卡
# 模型: mimo/mimo-v2.5
# 修复: 突袭有记录时剔除普通未通关（2026-06-02 bug修复）

"""#未通关 指令 - 查未通关关卡

规则：
- has_challenge: true 且两种难度都没过 → 分两行带标签
- has_challenge: false → 一行，不带标签
- 只过了一条 → 只显示没过的那条，带标签
- has_challenge: true 且突袭有记录但普通没记录 → 不显示
  （突袭记录可等效普通记录）
"""
import asyncio
import logging
import re

from api_client import WikiClient
from resolver.category import normalize_category
from formatter.uncleared import format_uncleared
from config import config

logger = logging.getLogger(__name__)


async def _resolve_uncleared(
    client: WikiClient,
    uncleared: list[dict],
    category: str,
) -> list[dict]:
    """根据实际查询记录，重建未通关列表。

    对 uncleared 中每个 has_challenge=True 的关卡查询记录，
    根据 normal/challenge 两种难度的实际记录情况决定显示：
    - 两种都没记录 → 显示两条（都未通关）
    - 只有 normal 有记录 → 显示一条 challenge（突袭未过）
    - 只有 challenge 有记录 → 不显示（突袭覆盖普通）
    - 两种都有记录 → 不显示（都已通关）

    has_challenge=False 的关卡原样保留。
    """
    # 分离有突袭和无突袭的关卡
    challenge_ops = [item for item in uncleared if item.get("hasChallenge")]
    non_challenge = [item for item in uncleared if not item.get("hasChallenge")]

    if not challenge_ops:
        return uncleared

    async def _query_record_types(op: str) -> set[str]:
        """查询关卡实际有哪些difficulty的记录。"""
        try:
            result = await client.query_records(operation=op, category=category)
            return {r.operation_type for r in result.records}
        except Exception:
            logger.warning(f"查询 {op} 记录失败，保守显示")
            return set()  # 查询失败时空集 → 显示两条，不误删

    # 并发查询所有有突袭的关卡
    ops = [item["operation"] for item in challenge_ops]
    results = await asyncio.gather(*[_query_record_types(op) for op in ops])

    resolved: list[dict] = []
    for item, has_records in zip(challenge_ops, results):
        has_normal = "normal" in has_records
        has_challenge_rec = "challenge" in has_records

        if has_normal and has_challenge_rec:
            # 两种都过了，不显示
            continue
        if has_challenge_rec and not has_normal:
            # 突袭过了，覆盖普通，不显示
            continue
        if has_normal and not has_challenge_rec:
            # 只过了普通，突袭没过 → 只显示 challenge
            resolved.append({
                "operation": item["operation"],
                "cn_name": item.get("cn_name", ""),
                "difficulty": "challenge",
                "hasChallenge": True,
            })
        else:
            # 都没过 → 显示两条
            resolved.append({
                "operation": item["operation"],
                "cn_name": item.get("cn_name", ""),
                "difficulty": "challenge",
                "hasChallenge": True,
            })
            resolved.append({
                "operation": item["operation"],
                "cn_name": item.get("cn_name", ""),
                "difficulty": "normal",
                "hasChallenge": True,
            })

    return non_challenge + resolved


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
            
            # 后处理：根据实际记录重建未通关列表
            uncleared = await _resolve_uncleared(
                client, result.uncleared, category,
            )
            
            # 格式化返回结果（传入 operation_index 以显示难度标签）
            return format_uncleared(result.episode, result.category, uncleared, operation_index)
    except Exception as e:
        logger.error(f"查询未通关关卡失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"
