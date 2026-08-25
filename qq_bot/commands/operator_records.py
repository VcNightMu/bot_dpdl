# -*- coding: utf-8 -*-
# 日期：2026-08-25
# 开发者：橘雪莉
# 功能摘要：#干员记录 指令 - 查询某干员在某流派的记录数（只回显个数）
# 模型：deepseek-v4-pro

"""#干员记录 指令 - 查干员在某流派的记录数"""
from __future__ import annotations

import json
import logging
import re

from api_client import WikiAPIValidationError, WikiClient
from config import config
from resolver.category import CATEGORIES, CATEGORY_ALIASES, normalize_category

logger = logging.getLogger(__name__)


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


async def handle_operator_records(
    match: re.Match,
    group_id: int,
    user_id: int,
    operation_index: dict | None = None,
) -> str:
    """处理 #干员记录 指令。

    格式: #干员记录 <干员> <流派>
    示例: #干员记录 羽毛笔 黎博利队

    使用 search-records 的 team + category 组合条件，只回显记录数。
    """
    args = match.group(1).strip()

    if not args:
        return (
            "缺少参数，格式：#干员记录 <干员> <流派>\n"
            "示例：#干员记录 羽毛笔 黎博利队"
        )

    parts = args.split()
    if len(parts) < 2:
        return (
            "缺少流派参数，格式：#干员记录 <干员> <流派>\n"
            "示例：#干员记录 羽毛笔 黎博利队"
        )

    # 最后一个词是流派，其余是干员名（兼容带空格的英文名如 "La Pluma"）
    category_input = parts[-1]
    operator_input = " ".join(parts[:-1])

    # 干员名误填成了流派名/别名（参数写反）时给出友好提示
    operator_stripped = operator_input.strip()
    if operator_stripped in CATEGORIES or operator_stripped in CATEGORY_ALIASES:
        return (
            f"「{operator_input}」是流派名，不是干员哦～\n"
            f"格式：#干员记录 <干员> <流派>\n"
            f"示例：#干员记录 羽毛笔 无精英满级"
        )

    category = normalize_category(category_input)
    if not category:
        return f"未找到流派 \"{category_input}\"，发送 #流派 查看所有流派"

    conditions = [
        {"field": "team", "value": {"members": [{"operator": operator_input}]}},
        {"field": "category", "value": category},
    ]

    logger.info("#干员记录: operator=%s, category=%s", operator_input, category)

    try:
        async with WikiClient(
            base_url=config.wiki_base_url,
            token=config.wiki_api_token,
        ) as client:
            result = await client.search_records(conditions=conditions)
    except WikiAPIValidationError as exc:
        msg = _extract_friendly_message(exc)
        return msg if msg else "查询参数有误，请检查输入"
    except Exception as exc:
        logger.error("查询干员记录失败: %s", exc, exc_info=True)
        return "查询失败，请稍后重试"

    count_valid = result.count_valid
    count = result.count

    if count_valid == 0:
        return f"「{operator_input}」在「{category}」没有找到记录"

    old_count = count - count_valid
    return (
        f"「{operator_input}」在「{category}」的记录统计：\n"
        f"总记录：{count} 条\n"
        f"有效记录：{count_valid} 条\n"
        f"旧纪录：{old_count} 条"
    )
