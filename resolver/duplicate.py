# 日期: 2026-06-11
# 开发者: 橘雪莉
# 功能: 关卡代号重复检测，跨活动同代号提示用户用中文名
# 模型: mimo/mimo-v2.5

"""关卡代号重复检测模块

当同一关卡代号出现在多个活动时，提示用户使用中文名查询。
"""
from __future__ import annotations


def check_duplicate_operation(
    operation_input: str,
    operation_index: dict | None,
    cmd_name: str = "#查",
) -> str | None:
    """检测关卡代号是否在多个活动中出现

    Args:
        operation_input: 用户输入的关卡代号
        operation_index: 关卡索引（含 duplicates）
        cmd_name: 指令名称，用于提示信息（如 "#查" 或 "#人数"）

    Returns:
        None: 无重复，正常进行
        str: 有重复，返回提示信息
    """
    if not operation_index:
        return None

    from resolver.operation import normalize_operation
    normalized = normalize_operation(operation_input)

    duplicates = operation_index.get("duplicates", {})
    if normalized in duplicates:
        dupes = duplicates[normalized]
        # 格式：中文名（活动名）
        names = [f"{d['cn_name']}（{d['episode']}）" for d in dupes]
        name_list = "、".join(names)
        first_cn = dupes[0]["cn_name"]
        return (
            f"关卡 {operation_input} 对应多个关卡：{name_list}\n"
            f"请使用中文名查询，例如：{cmd_name} {first_cn}"
        )

    return None
