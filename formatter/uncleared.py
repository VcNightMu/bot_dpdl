# 日期: 2026-06-02
# 开发者: 宝生玛格
# 功能: #未通关指令格式化模块，展示未通关关卡列表
# 模型: mimo/mimo-v2.5

"""#未通关 格式化模块

展示规则：
- has_challenge: true 且两种难度都没过 → 分两行带标签
- has_challenge: false → 一行，不带标签
- 只过了一条 → 只显示没过的那条，带标签
"""
from __future__ import annotations

from typing import Any


def format_uncleared(
    episode: str,
    category: str,
    uncleared: list[dict[str, Any]],
    operation_index: dict[str, dict[str, Any]] | None = None,
) -> str:
    """格式化未通关结果

    episode: 活动名
    category: 流派名
    uncleared: 未通关关卡列表
    operation_index: 关卡索引（用于查询 has_challenge）
    """
    if not uncleared:
        return f"📌 {episode} · {category} 所有关卡已通关 🎉"

    total = len(uncleared)
    header = f"📌 {episode} · {category} 未通关关卡（{total}个）\n"

    lines: list[str] = []
    for item in uncleared:
        operation = item.get("operation", "???")
        cn_name = item.get("cn_name", "")
        difficulty = item.get("difficulty", "normal")

        # 查询 has_challenge 信息
        has_challenge = False
        if operation_index:
            info = operation_index.get("by_operation", {}).get(operation.upper())
            if info:
                has_challenge = info.get("has_challenge", False)

        # 构建标签
        label = ""
        if has_challenge:
            # 有突袭模式时，显示难度标签
            if difficulty == "challenge":
                label = " [突袭]"
            else:
                label = " [普通]"

        # 格式化关卡名
        name_part = f"{operation} {cn_name}" if cn_name else operation
        lines.append(f"❌ {name_part}{label}")

    return header + "\n".join(lines)
