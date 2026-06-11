# 日期: 2026-06-11
# 开发者: 橘雪莉
# 功能: 活动缩写解析模块，支持主线章节缩写和活动缩写查询
# 模型: mimo/mimo-v2.5

"""活动缩写解析模块

支持两种缩写查询：
1. 主线关卡：支持 "第X章"、"第X"、纯数字 格式
2. 非主线关卡：使用活动缩写（从 operation_index 动态构建）

当一个缩写对应多个活动时，返回所有匹配的活动名供用户选择。
"""
from __future__ import annotations

import re
from typing import Any


# 主线关卡缩写映射（硬编码，数据固定不变）
# 格式: 缩写 → 活动全名
_MAINLINE_MAP: dict[str, str] = {
    # 第零章
    "第零章": "黑暗时代·上",
    "第0章": "黑暗时代·上",
    "0": "黑暗时代·上",
    # 第一章
    "第一章": "黑暗时代·下",
    "第1章": "黑暗时代·下",
    "1": "黑暗时代·下",
    # 第二章
    "第二章": "异卵同生",
    "第2章": "异卵同生",
    "2": "异卵同生",
    # 第三章
    "第三章": "二次呼吸",
    "第3章": "二次呼吸",
    "3": "二次呼吸",
    # 第四章
    "第四章": "急性衰竭",
    "第4章": "急性衰竭",
    "4": "急性衰竭",
    # 第五章
    "第五章": "靶向药物",
    "第5章": "靶向药物",
    "5": "靶向药物",
    # 第六章
    "第六章": "局部坏死",
    "第6章": "局部坏死",
    "6": "局部坏死",
    # 第七章
    "第七章": "苦难摇篮",
    "第7章": "苦难摇篮",
    "7": "苦难摇篮",
    # 第八章
    "第八章": "怒号光明",
    "第8章": "怒号光明",
    "8": "怒号光明",
    # 第九章
    "第九章": "风暴瞭望",
    "第9章": "风暴瞭望",
    "9": "风暴瞭望",
    # 第十章
    "第十章": "破碎日冕",
    "第10章": "破碎日冕",
    "10": "破碎日冕",
    # 第十一章
    "第十一章": "淬火尘霾",
    "第11章": "淬火尘霾",
    "11": "淬火尘霾",
    # 第十二章
    "第十二章": "惊霆无声",
    "第12章": "惊霆无声",
    "12": "惊霆无声",
    # 第十三章
    "第十三章": "恶兆湍流",
    "第13章": "恶兆湍流",
    "13": "恶兆湍流",
    # 第十四章
    "第十四章": "慈悲灯塔",
    "第14章": "慈悲灯塔",
    "14": "慈悲灯塔",
    # 第十五章
    "第十五章": "离解复合",
    "第15章": "离解复合",
    "15": "离解复合",
    # 第十六章
    "第十六章": "反常光谱",
    "第16章": "反常光谱",
    "16": "反常光谱",
    # 第十七章
    "第十七章": "相变临界",
    "第17章": "相变临界",
    "17": "相变临界",
}

# 非主线关卡缩写映射（从 operation_index 动态构建）
# 缩写 → 活动全名列表（可能有多个）
_NON_MAINLINE_MAP: dict[str, list[str]] = {}

# 构建标志
_BUILT_FROM_INDEX = False


def _extract_prefix(operation: str) -> str:
    """从关卡代号中提取前缀字母部分
    
    示例:
        H11-1 → H
        M8-8 → M
        SV-5 → SV
        GT-EX-1 → GT
        CB-10 → CB
    """
    # 匹配开头的字母部分（可能包含连字符后的字母）
    match = re.match(r'^([A-Za-z]+)', operation)
    if match:
        return match.group(1).upper()
    return ""


def build_episode_short_map(operation_index: dict[str, Any]) -> dict[str, list[str]]:
    """从 operation_index 动态构建活动缩写映射
    
    遍历所有关卡，提取代号前缀，映射到对应的活动名。
    同一个前缀可能对应多个活动（如 SV 对应多个活动）。
    
    Args:
        operation_index: 关卡索引，包含 by_operation 字典
        
    Returns:
        缩写 → 活动名列表 的映射
    """
    prefix_to_episodes: dict[str, set[str]] = {}
    
    by_operation = operation_index.get("by_operation", {})
    
    for op_code, info in by_operation.items():
        episode = info.get("episode", "")
        if not episode:
            continue
        
        prefix = _extract_prefix(op_code)
        if not prefix:
            continue
        
        # 跳过主线关卡代号（H、M 开头的是主线）
        # 主线代号格式: H11-1, M8-8 等
        if re.match(r'^[HM]\d', op_code):
            continue
        
        if prefix not in prefix_to_episodes:
            prefix_to_episodes[prefix] = set()
        prefix_to_episodes[prefix].add(episode)
    
    # 转换为 list 格式
    return {prefix: list(episodes) for prefix, episodes in prefix_to_episodes.items()}


def init_episode_short_map(operation_index: dict[str, Any]) -> None:
    """初始化非主线活动缩写映射
    
    应在应用启动时调用一次。
    """
    global _NON_MAINLINE_MAP, _BUILT_FROM_INDEX
    
    if _BUILT_FROM_INDEX:
        return
    
    _NON_MAINLINE_MAP = build_episode_short_map(operation_index)
    _BUILT_FROM_INDEX = True


def resolve_episode_short(user_input: str) -> tuple[str, list[str]] | None:
    """解析活动缩写，返回 (原始输入, 匹配的活动全名列表)
    
    Returns:
        None: 未找到匹配
        (input, [names]): 匹配成功，返回活动名列表
    """
    if not user_input or not user_input.strip():
        return None
    
    stripped = user_input.strip()
    
    # 1. 尝试主线缩写匹配（支持 "第X章"、纯数字）
    if stripped in _MAINLINE_MAP:
        return (stripped, [_MAINLINE_MAP[stripped]])
    
    # 2. 尝试非主线缩写匹配（大小写不敏感）
    upper = stripped.upper()
    if upper in _NON_MAINLINE_MAP:
        return (stripped, _NON_MAINLINE_MAP[upper])
    
    return None


def format_episode_choices(names: list[str], cmd_name: str = "#未通关") -> str:
    """格式化多个活动名的选择提示"""
    if len(names) == 1:
        return names[0]
    
    name_list = "、".join(names)
    return (
        f"缩写对应多个活动：{name_list}\n"
        f"请使用完整活动名查询，例如：{cmd_name} {names[0]}"
    )
