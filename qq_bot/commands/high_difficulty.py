# 日期: 2026-10-10
# 开发者: 橘雪莉
# 功能: #高难指令 - 按活动名和流派查询高难关卡（该流派最少 10 人及以上）
# 模型: deepseek-flash

"""#高难 指令 - 查该流派 10 人及以上的关卡。

格式: #高难 <活动名> <流派>
示例: #高难 巴别塔 四星队

数据链路：GET /menu（启动时已建索引）解析活动名
        → POST /search-records（category + episode）一次取回该活动全部记录
        → 本地按 (关卡 × 难度) 取最少人，筛出 >= 10 的
"""
import logging
import re

from config import config
from api_client import WikiClient
from resolver.command_args import parse_episode_category
from resolver.episode import resolve_aggregate_episodes
from resolver.episode_short import resolve_episode_short, format_episode_choices
from resolver.high_difficulty import HIGH_TEAM_THRESHOLD, find_high_difficulty
from formatter.high_difficulty import format_high_difficulty

logger = logging.getLogger(__name__)


async def handle_high_difficulty(
    match: re.Match,
    group_id: int,
    user_id: int,
    operation_index: dict | None = None,
) -> str | list[str]:
    """处理 #高难 指令。"""
    args = match.group(1).strip()

    parsed = parse_episode_category(args, "#高难 <活动名> <流派>")
    if parsed.error:
        return parsed.error

    episode_input = parsed.episode
    category = parsed.category

    logger.info(f"#高难指令: episode={episode_input}, category={category}")

    # 聚合活动（如「剿灭」→ 多个 episode）
    agg_episodes = resolve_aggregate_episodes(episode_input)

    if agg_episodes:
        episodes = list(agg_episodes)
        display_name = episode_input
    else:
        short_result = resolve_episode_short(episode_input)
        if short_result:
            _, names = short_result
            if len(names) > 1:
                return format_episode_choices(names, "#高难")
            episodes = [names[0]]
            display_name = names[0]
        else:
            episodes = [episode_input]
            display_name = episode_input

    try:
        async with WikiClient(
            base_url=config.wiki_base_url,
            token=config.wiki_api_token,
        ) as client:
            all_hits = []
            truncated = False
            for episode in episodes:
                result = await client.search_records(conditions=[
                    {"field": "category", "value": category},
                    {"field": "episode", "value": episode},
                ])
                if result.count > len(result.records):
                    truncated = True
                hits = find_high_difficulty(
                    result.records,
                    threshold=HIGH_TEAM_THRESHOLD,
                    operation_index=operation_index,
                )
                all_hits.extend(hits)

        # 同关卡可能被多个 episode 命中（聚合场景），去重
        seen: set[tuple[str, str]] = set()
        deduped = []
        for hit in all_hits:
            key = (hit.operation.upper(), hit.difficulty)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(hit)
        deduped.sort(key=lambda r: (-r.min_team_size, r.operation, r.difficulty))

        return format_high_difficulty(
            display_name,
            category,
            deduped,
            threshold=HIGH_TEAM_THRESHOLD,
            truncated=truncated,
        )
    except Exception as e:
        logger.error(f"查询高难关卡失败: {e}", exc_info=True)
        return "查询失败，请稍后重试"
