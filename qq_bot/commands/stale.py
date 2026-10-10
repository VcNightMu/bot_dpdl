# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: #待压人指令 - 按活动名、流派和天数查询待压人记录，支持缩写查询
# 模型: mimo/mimo-v2.5

"""#待压人 指令 - 查待压人记录"""
import logging
import re

from api_client import WikiClient
from config import config
from resolver.category import normalize_category
from resolver.command_args import parse_episode_category
from resolver.episode import resolve_aggregate_episodes
from resolver.episode_short import resolve_episode_short, format_episode_choices
from formatter.stale import format_stale

logger = logging.getLogger(__name__)


async def handle_stale(match: re.Match, group_id: int, user_id: int, operation_index: dict | None = None) -> str:
    """
    处理 #待压人 指令
    格式: #待压人 <活动名> <流派> [天数]
    示例: #待压人 惊霆无声 四星队 365
    支持缩写查询: #待压人 SV 四星队
    """
    args = match.group(1).strip()

    # 解析参数：活动名 + 流派 + 可选天数
    # （活动名可能含空格，交给 parse_episode_category 处理）
    parsed = parse_episode_category(
        args,
        "#待压人 <活动名> <流派> [天数]",
        allow_days=True,
    )
    if parsed.error:
        return parsed.error

    episode_input = parsed.episode
    category = parsed.category
    days = parsed.days if parsed.days is not None else config.default_stale_days
    
    # 尝试聚合活动解析（如"剿灭"→多个episode）
    agg_episodes = resolve_aggregate_episodes(episode_input)
    if agg_episodes:
        logger.info(f"#待压人指令(聚合): episodes={agg_episodes}, category={category}, days={days}")
        try:
            async with WikiClient(base_url=config.wiki_base_url, token=config.wiki_api_token) as client:
                all_stale = []
                seen: set[tuple] = set()
                for ep in agg_episodes:
                    result = await client.stale_records(episode=ep, category=category, days=days)
                    for item in result.stale:
                        key = (
                            item.get("operation", "").upper(),
                            item.get("cn_name", "").strip(),
                            item.get("difficulty", "normal"),
                        )
                        if key not in seen:
                            seen.add(key)
                            all_stale.append(item)
                return format_stale(episode_input, category, days, all_stale)
        except Exception as e:
            logger.error(f"查询待压人记录失败: {e}", exc_info=True)
            return "查询失败，请稍后重试"
    
    # 尝试缩写解析
    short_result = resolve_episode_short(episode_input)
    if short_result:
        _, names = short_result
        if len(names) > 1:
            # 缩写对应多个活动，提示用户选择
            return format_episode_choices(names, "#待压人")
        episode = names[0]
    else:
        # 不是缩写，直接使用输入的活动名
        episode = episode_input
    
    logger.info(f"#待压人指令: episode={episode}, category={category}, days={days}")
    
    try:
        # 调用wiki API查询待压人记录
        async with WikiClient(base_url=config.wiki_base_url, token=config.wiki_api_token) as client:
            result = await client.stale_records(episode=episode, category=category, days=days)
            
            # 格式化返回结果
            return format_stale(result.episode, result.category, result.days, result.stale)
    except Exception as e:
        logger.error(f"查询待压人记录失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"
