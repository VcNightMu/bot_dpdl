# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: 关卡名精确匹配模块，支持 operation 代号和 cn_name 中文名匹配
# 模型: mimo/mimo-v2.5

"""关卡名精确匹配模块

两种匹配方式：
1. operation 代号精确匹配（大小写不敏感）
2. cn_name 中文名精确匹配

不支持模糊查找。
"""
from __future__ import annotations

import re
from typing import Any


def normalize_operation(raw: str) -> str:
    """把用户输入的关卡代号归一化（大小写、空格→连字符）

    示例：
        M8 8 → M8-8
        h11-1 → H11-1
        gt ex1 → GT-EX-1
    """
    s = raw.strip().upper()
    s = re.sub(r"\s+", "-", s)  # 空格→连字符
    # 在字母和数字之间插入连字符（跳过已有连字符）
    # 策略：先拆分 token（字母组、数字组、连字符），再在需要的地方插入连字符
    tokens: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "-":
            tokens.append("-")
            i += 1
        elif ch.isalpha():
            j = i
            while j < len(s) and s[j].isalpha():
                j += 1
            tokens.append(s[i:j])
            i = j
        elif ch.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            tokens.append(s[i:j])
            i = j
        else:
            tokens.append(ch)
            i += 1

    # 在字母组和数字组之间插入连字符（如果没有的话）
    result: list[str] = []
    for idx, token in enumerate(tokens):
        result.append(token)
        if idx + 1 < len(tokens):
            cur = token
            nxt = tokens[idx + 1]
            # 字母→数字：检查后续是否已有连字符
            if cur.isalpha() and nxt.isdigit():
                # 向后看，如果数字后面紧跟连字符（如 M8-8 中的 8-），不插入
                has_hyphen_after = False
                for j in range(idx + 2, len(tokens)):
                    if tokens[j] == "-":
                        has_hyphen_after = True
                        break
                    elif not tokens[j].isdigit():
                        break  # 遇到非数字非连字符，停止
                if not has_hyphen_after:
                    result.append("-")
            # 数字→字母：检查是否已有连字符
            elif cur.isdigit() and nxt.isalpha():
                # 如果前一个 token 是连字符，不插入
                if idx > 0 and tokens[idx - 1] == "-":
                    pass
                else:
                    result.append("-")
    return "".join(result)


def build_operation_index(menu_data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """从 menu 树构建关卡索引

    返回两个字典：
    - by_operation: { "M8-8": { cn_name, episode, story, has_challenge }, ... }
    - by_cn_name:   { "破碎日冕": { operation, episode, story, has_challenge }, ... }
    """
    by_operation: dict[str, dict[str, Any]] = {}
    by_cn_name: dict[str, dict[str, Any]] = {}

    for story_node in menu_data:
        story = story_node.get("story", "")
        for episode_node in story_node.get("episodes", []):
            episode = episode_node.get("episode", "")
            for op_node in episode_node.get("operations", []):
                operation = op_node.get("operation", "")
                cn_name = op_node.get("cn_name", "")
                has_challenge = op_node.get("hasChallenge", False)

                info = {
                    "operation": operation,
                    "cn_name": cn_name,
                    "episode": episode,
                    "story": story,
                    "has_challenge": has_challenge,
                }

                # 代号索引（key 为大写）
                by_operation[operation.upper()] = info

                # 中文名索引
                if cn_name:
                    by_cn_name[cn_name] = info

    return {"by_operation": by_operation, "by_cn_name": by_cn_name}


def resolve_operation(
    user_input: str, menu_index: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], str] | None:
    """精确匹配关卡名

    返回: (关卡信息字典, 匹配方式) 或 None
    匹配方式: "operation" | "cn_name"
    """
    if not user_input or not user_input.strip():
        return None

    # 1. 精确匹配 operation（大小写不敏感，先归一化）
    normalized = normalize_operation(user_input)
    if normalized in menu_index.get("by_operation", {}):
        return menu_index["by_operation"][normalized], "operation"

    # 2. 精确匹配 cn_name
    stripped = user_input.strip()
    if stripped in menu_index.get("by_cn_name", {}):
        return menu_index["by_cn_name"][stripped], "cn_name"

    return None
