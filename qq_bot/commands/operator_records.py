# -*- coding: utf-8 -*-
# 日期：2026-08-27
# 开发者：橘雪莉
# 功能摘要：#干员记录 指令 - 查询干员在某流派的记录数（支持单干员、多干员组合）
# 模型：deepseek-v4-pro

"""#干员记录 指令 - 查干员在某流派的记录数

语法（两种均需限定流派）：
1. #干员记录 <干员> <流派>             — 单干员在某流派的记录数
2. #干员记录 <干员A>+<干员B>+... <流派> — 多干员同时上场、且属于某流派的记录数
"""
from __future__ import annotations

import json
import logging
import re

from api_client import WikiAPIValidationError, WikiClient
from config import config
from resolver.category import CATEGORIES, CATEGORY_ALIASES, normalize_category

logger = logging.getLogger(__name__)

# team 条件 members 上限（一个关卡最多带 13 人）
MAX_COMBO_OPERATORS = 13


def _extract_friendly_message(exc: WikiAPIValidationError) -> str | None:
    """从 400 校验错误中提取服务端返回的友好提示（如「干员「xxx」未识别」）。

    WikiAPIValidationError.message 形如：
        请求参数有误: {"error":"bad_request","message":"干员「xxx」未识别"}
    """
    try:
        idx = exc.message.find("{")
        if idx >= 0:
            data = json.loads(exc.message[idx:])
            if isinstance(data, dict) and data.get("message"):
                return data["message"]
    except Exception:
        pass
    return None


def _parse_combo(args: str) -> list[str]:
    """按 + 号分割干员名，去空白、去空项、去重（保序）。"""
    result: list[str] = []
    seen: set[str] = set()
    for part in args.split("+"):
        name = part.strip()
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


async def _search_records(conditions: list[dict]):
    """执行 search-records，返回 (SearchResult, None) 或 (None, 错误消息)。"""
    try:
        async with WikiClient(
            base_url=config.wiki_base_url,
            token=config.wiki_api_token,
        ) as client:
            result = await client.search_records(conditions=conditions)
        return result, None
    except WikiAPIValidationError as exc:
        msg = _extract_friendly_message(exc)
        return None, (msg if msg else "查询参数有误，请检查输入")
    except Exception as exc:
        logger.error("查询干员记录失败: %s", exc, exc_info=True)
        return None, "查询失败，请稍后重试"


async def handle_operator_records(
    match: re.Match,
    group_id: int,
    user_id: int,
    operation_index: dict | None = None,
) -> str:
    """处理 #干员记录 指令。

    格式一: #干员记录 <干员> <流派>
      示例: #干员记录 羽毛笔 无精英满级
    格式二: #干员记录 <干员A>+<干员B>+... <流派>
      示例: #干员记录 羽毛笔+银灰 无精英满级

    组合查询限定在某个流派上，team.members 为 AND（同时上场）关系。
    """
    args = match.group(1).strip()

    if not args:
        return (
            "缺少参数，格式：#干员记录 <干员> <流派>\n"
            "或：#干员记录 <干员A>+<干员B> <流派> 查组合记录\n"
            "示例：#干员记录 羽毛笔 无精英满级"
        )

    # 最后一个空格分隔「干员部分」和「流派」（兼容带空格的英文名如 "La Pluma"）
    parts = args.rsplit(maxsplit=1)
    if len(parts) < 2:
        return (
            "缺少流派参数，格式：#干员记录 <干员> <流派>\n"
            "示例：#干员记录 羽毛笔 无精英满级\n"
            "组合：#干员记录 羽毛笔+银灰 无精英满级"
        )

    operator_part = parts[0].strip()
    category_input = parts[1].strip()

    # 干员部分含 + 号 → 组合查询（team.members 多干员 AND）
    if "+" in operator_part:
        operators = _parse_combo(operator_part)
        if len(operators) < 2:
            return (
                "组合查询至少需要两个干员，格式：#干员记录 <干员A>+<干员B> <流派>\n"
                "示例：#干员记录 羽毛笔+银灰 无精英满级"
            )
        if len(operators) > MAX_COMBO_OPERATORS:
            return f"最多支持 {MAX_COMBO_OPERATORS} 个干员的组合查询"

        operator_display = "+".join(operators)
        members = [{"operator": op} for op in operators]
        is_combo = True
    else:
        # 干员名误填成了流派名/别名（参数写反）时给出友好提示
        if operator_part in CATEGORIES or operator_part in CATEGORY_ALIASES:
            return (
                f"「{operator_part}」是流派名，不是干员哦～\n"
                f"格式：#干员记录 <干员> <流派>\n"
                f"示例：#干员记录 羽毛笔 无精英满级"
            )
        operator_display = operator_part
        members = [{"operator": operator_part}]
        is_combo = False

    category = normalize_category(category_input)
    if not category:
        return f"未找到流派 \"{category_input}\"，发送 #流派 查看所有流派"

    conditions = [
        {"field": "team", "value": {"members": members}},
        {"field": "category", "value": category},
    ]

    logger.info(
        "#干员记录: operator=%s, category=%s, combo=%s",
        operator_display,
        category,
        is_combo,
    )

    result, error = await _search_records(conditions)
    if error:
        return error

    count_valid = result.count_valid
    count = result.count

    if count_valid == 0:
        if is_combo:
            return f"「{operator_display}」在「{category}」没有找到同时上场的记录"
        return f"「{operator_display}」在「{category}」没有找到记录"

    old_count = count - count_valid

    # 合约记录单独统计（危机合约 + 危机合约Re，因合约非常驻）
    # 合约记录仅统计有效合约记录，合约旧纪录计入旧纪录行
    contract_count = 0
    for story_name in ("危机合约", "危机合约Re"):
        c_result, c_error = await _search_records(
            conditions + [{"field": "story", "value": story_name}]
        )
        if c_error is None:
            contract_count += c_result.count_valid

    # 有效记录 = 非合约的有效记录（合约有效已单独列为合约记录）
    effective_count = count_valid - contract_count

    label = "同时上场的记录统计" if is_combo else "记录统计"
    return (
        f"「{operator_display}」在「{category}」的{label}：\n"
        f"总记录：{count} 条\n"
        f"有效记录：{effective_count} 条\n"
        f"合约记录：{contract_count} 条\n"
        f"旧纪录：{old_count} 条"
    )
