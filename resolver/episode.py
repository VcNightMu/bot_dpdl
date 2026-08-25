# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: 活动名精确匹配模块，用于 #未通关 和 #待压人 指令，支持聚合活动
# 模型: mimo/mimo-v2.5

"""活动名精确匹配模块

精确匹配 episode 名称，用于 #未通关 和 #待压人 指令。
另支持"聚合活动"：一个名称对应多个 episode，查询时合并结果（如剿灭作战）。
"""
from __future__ import annotations

from typing import Any


# 聚合活动：一个名称对应多个 episode，查询时合并展示
# 剿灭作战下分"长期委托"/"轮换委托"，语义上都是剿灭，用户希望不区分
AGGREGATE_EPISODES: dict[str, list[str]] = {
    "剿灭": ["长期委托", "轮换委托"],
    "剿灭作战": ["长期委托", "轮换委托"],
}


def resolve_aggregate_episodes(user_input: str) -> list[str] | None:
    """识别聚合活动名，返回对应的 episode 列表

    Args:
        user_input: 用户输入的活动名

    Returns:
        None: 不是聚合活动
        list[str]: 聚合活动对应的 episode 列表（按展示顺序）
    """
    if not user_input or not user_input.strip():
        return None
    return AGGREGATE_EPISODES.get(user_input.strip())


def build_episode_index(menu_data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """从 menu 树构建活动索引

    返回: { "惊霆无声": { story, operations: [...] }, ... }
    """
    index: dict[str, dict[str, Any]] = {}

    for story_node in menu_data:
        story = story_node.get("story", "")
        for episode_node in story_node.get("episodes", []):
            episode = episode_node.get("episode", "")
            operations = episode_node.get("operations", [])
            index[episode] = {
                "story": story,
                "episode": episode,
                "operations": operations,
            }

    return index


def resolve_episode(
    user_input: str, episode_index: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """精确匹配活动名

    返回: 活动信息字典或 None
    """
    if not user_input or not user_input.strip():
        return None

    stripped = user_input.strip()
    return episode_index.get(stripped)
