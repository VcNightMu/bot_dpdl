# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: 活动名精确匹配模块，用于 #未通关 和 #待压人 指令
# 模型: mimo/mimo-v2.5

"""活动名精确匹配模块

精确匹配 episode 名称，用于 #未通关 和 #待压人 指令。
"""
from __future__ import annotations

from typing import Any


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
