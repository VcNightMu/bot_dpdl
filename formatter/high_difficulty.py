# 日期: 2026-10-10
# 开发者: 橘雪莉
# 功能: #高难指令格式化模块，展示该流派需要 10 人及以上才能通关的关卡
# 模型: deepseek-flash

"""#高难 格式化模块。

展示格式：

    💀 巴别塔 · 四星队 高难关卡（最少 10 人及以上，2个）

    🔴 BB-S-4 巴别塔-S-4 [普通] — 最少 10 人 | 共 3 条记录
       1. BV1xxxxxxx（10人）
       2. BV1yyyyyyy（10人）
    🔴 BB-S-4 巴别塔-S-4 [突袭] — 最少 12 人 | 共 1 条记录
       1. BV1zzzzzzz（12人）

超过单条消息长度上限时自动拆成多条。
"""
from __future__ import annotations

from typing import Any

from resolver.high_difficulty import HIGH_TEAM_THRESHOLD, _field
from .record import MAX_MSG_LENGTH
from .video import format_video_link


def format_high_difficulty(
    episode: str,
    category: str,
    hits: list[Any],
    *,
    threshold: int = HIGH_TEAM_THRESHOLD,
    truncated: bool = False,
) -> str | list[str]:
    """格式化高难查询结果。

    episode: 活动名
    category: 流派名
    hits: resolver.high_difficulty.find_high_difficulty 的返回值
    threshold: 高难阈值（用于文案）
    truncated: 数据是否因分页被截断（count > 返回条数）

    返回单条消息字符串，或过长时返回消息列表。
    """
    if not hits:
        return (
            f"💀 {episode} · {category} 无高难关卡\n"
            f"（该活动下没有「最少 {threshold} 人及以上」的关卡）"
        )

    header = (
        f"💀 {episode} · {category} 高难关卡"
        f"（最少 {threshold} 人及以上，{len(hits)}个）"
    )

    blocks: list[str] = []
    for hit in hits:
        name_part = f"{hit.operation} {hit.cn_name}".strip() if hit.cn_name else hit.operation
        lines = [
            f"🔴 {name_part}{hit.difficulty_label} — "
            f"最少 {hit.min_team_size} 人 | 共 {hit.total_records} 条记录"
        ]
        for i, rec in enumerate(hit.best_records, 1):
            team_size = len(_field(rec, "team", default=[]) or [])
            link = format_video_link(_field(rec, "url", default="") or "")
            lines.append(f"   {i}. {link}（{team_size}人）")
        blocks.append("\n".join(lines))

    notes: list[str] = []
    if truncated:
        notes.append("⚠️ 该活动记录数超过单页上限，结果可能不完整")

    # 组装并按长度切分
    messages: list[str] = []
    current = header + ("\n" + "\n".join(notes) if notes else "")
    for block in blocks:
        chunk = "\n" + block
        if len(current) + len(chunk) > MAX_MSG_LENGTH:
            messages.append(current)
            current = block
        else:
            current += chunk
    if current:
        messages.append(current)

    return messages[0] if len(messages) == 1 else messages
