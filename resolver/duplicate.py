# 日期: 2026-06-11
# 开发者: 橘雪莉
# 功能: 关卡重复检测，代号或中文名对应多个关卡时提示用户精确查询
# 模型: mimo/mimo-v2.5

"""关卡重复检测模块

当同一关卡代号（含剿灭地区名）或中文名对应多个关卡时，提示用户用更精确的方式查询：
- 代号重复 → 提示用中文名
- 中文名重复 → 提示用关卡代号
"""
from __future__ import annotations


def check_duplicate_operation(
    operation_input: str,
    operation_index: dict | None,
    cmd_name: str = "#查",
) -> str | None:
    """检测关卡代号或中文名是否对应多个关卡

    Args:
        operation_input: 用户输入的关卡代号或中文名
        operation_index: 关卡索引（含 duplicates / cn_name_duplicates）
        cmd_name: 指令名称，用于提示信息（如 "#查" 或 "#人数"）

    Returns:
        None: 无重复，正常进行
        str: 有重复，返回提示信息
    """
    if not operation_index:
        return None

    from resolver.operation import normalize_operation

    # 1. 代号（含剿灭地区名）重复检测
    normalized = normalize_operation(operation_input)
    duplicates = operation_index.get("duplicates", {})
    if normalized in duplicates:
        dupes = duplicates[normalized]
        names = [f"{d['cn_name']}（{d['episode']}）" for d in dupes]
        name_list = "、".join(names)
        first_cn = dupes[0]["cn_name"]
        return (
            f"关卡 {operation_input} 对应多个关卡：{name_list}\n"
            f"请使用中文名查询，例如：{cmd_name} {first_cn}"
        )

    # 2. 中文名重复检测
    stripped = operation_input.strip()
    cn_duplicates = operation_index.get("cn_name_duplicates", {})
    if stripped in cn_duplicates:
        dupes = cn_duplicates[stripped]
        names = [f"{d['operation']}（{d['episode']}）" for d in dupes]
        name_list = "、".join(names)
        first_op = dupes[0]["operation"]
        return (
            f"关卡中文名 {operation_input} 对应多个关卡：{name_list}\n"
            f"请使用关卡代号查询，例如：{cmd_name} {first_op}"
        )

    return None
