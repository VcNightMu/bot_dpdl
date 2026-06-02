# 日期: 2026-06-02
# 开发者: 宝生玛格
# 功能: #未通关指令格式化模块，展示未通关关卡列表
# 模型: mimo/mimo-v2.5
# 修复: 突袭关卡双难度补全逻辑（2026-06-02 bug修复）

"""#未通关 格式化模块

展示规则：
- has_challenge: true 且两种难度都没过 → 分两行带标签
- has_challenge: false → 一行，不带标签
- 只过了一条 → 只显示没过的那条，带标签
- has_challenge: true 且突袭有记录但普通无记录 → 不显示
  （突袭记录可等效普通记录）
"""
from __future__ import annotations

from typing import Any


def _supplement_challenge_variants(
    uncleared: list[dict[str, Any]],
    operation_index: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """补全突袭关卡的双难度variant。

    API 可能只返回一个 difficulty variant（通常是 challenge），
    对于 has_challenge=True 的关卡，需要确保两种难度都出现。

    补全规则：
    - has_challenge=True 且只收到 challenge → 补上 normal
    - has_challenge=True 且只收到 normal → 补上 challenge
    - has_challenge=False 或已收到两种 → 不动
    """
    if not operation_index:
        return uncleared

    # 按 operation 分组，记录已有哪些 difficulty
    by_op: dict[str, list[dict[str, Any]]] = {}
    for item in uncleared:
        op = item.get("operation", "???").upper()
        by_op.setdefault(op, []).append(item)

    result = list(uncleared)  # 复制一份
    appended: list[dict[str, Any]] = []

    for op, items in by_op.items():
        info = operation_index.get("by_operation", {}).get(op)
        if not info or not info.get("has_challenge", False):
            continue

        difficulties = {item.get("difficulty", "normal") for item in items}
        if len(difficulties) >= 2:
            continue  # 已经有两种，不用补

        # 从已有 item 取公共字段作为模板
        template = items[0]
        missing_diff = "normal" if "challenge" in difficulties else "challenge"

        appended.append({
            "operation": template.get("operation", "???"),
            "cn_name": template.get("cn_name", ""),
            "difficulty": missing_diff,
        })

    return result + appended


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

    # 补全突袭关卡的双难度 variant
    uncleared = _supplement_challenge_variants(uncleared, operation_index)

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
