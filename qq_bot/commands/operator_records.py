# -*- coding: utf-8 -*-
# 日期：2026-08-27
# 开发者：橘雪莉
# 功能摘要：#干员记录 指令 - 查询干员在某流派的记录数（支持单干员、组合、指定技能）
# 模型：deepseek-v4-pro

"""#干员记录 指令 - 查干员在某流派的记录数

语法（均需限定流派）：
1. #干员记录 <干员> <流派>              — 任意技能
2. #干员记录 <干员>1 <流派>             — 只统计使用该干员 1 技能的记录
3. #干员记录 <干员A>+<干员B> <流派>     — 多干员同时上场
4. #干员记录 <干员A>1+<干员B>3 <流派>   — 组合查询，且各自指定技能

技能号写在干员名后面（1/2/3），不写表示任意技能。

关于「名字本身以数字结尾」的干员（Castle-3、Lancet-2 等）：
目前**所有数字结尾的干员都是 1 星小车，本身没有技能**，
所以「先按技能号拆、拆错就回退为完整干员名」的做法永远安全 ——
回退不会丢掉任何合法的技能筛选（真正有技能的干员名不会以数字结尾）。
实现上不维护机器人名单：交给 API 报「干员未识别」来触发回退，
将来新增同名规则的干员也不会出错。
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

# 干员名 + 尾部技能号（1/2/3）。名字至少 1 个字符，所以 "3" 这类纯数字不会命中。
SKILL_SUFFIX_RE = re.compile(r"^(?P<name>.+?)(?P<skill>[123])$")

# API 校验错误里的「干员「xxx」未识别」
UNRECOGNIZED_RE = re.compile(r"干员[「\"]([^」\"]+)[」\"]未识别")


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


def _extract_unrecognized_name(message: str) -> str | None:
    """从友好提示中取出未被识别的干员名（用于技能号回退）。"""
    m = UNRECOGNIZED_RE.search(message or "")
    return m.group(1) if m else None


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


def _split_operator_skill(token: str) -> tuple[str, str | None]:
    """把「银灰1」拆成 ("银灰", "1")；「银灰」返回 ("银灰", None)。

    名字本身以数字结尾时（如 Castle-3）这里会先拆成 ("Castle-", "3")，
    由调用方在 API 报「未识别」后回退。
    """
    token = (token or "").strip()
    m = SKILL_SUFFIX_RE.match(token)
    if not m:
        return token, None
    return m.group("name"), m.group("skill")


def _display(items: list[dict]) -> str:
    """用于回复文案的干员展示：银灰（1技能）+艾雅法拉。"""
    parts = []
    for it in items:
        parts.append(f"{it['name']}（{it['skill']}技能）" if it["skill"] else it["name"])
    return "+".join(parts)


def _build_members(items: list[dict]) -> list[dict]:
    members = []
    for it in items:
        if it["skill"]:
            members.append({"operator": it["name"], "skill": it["skill"]})
        else:
            members.append({"operator": it["name"]})
    return members


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
    格式二: #干员记录 <干员>1 <流派>
      示例: #干员记录 银灰3 常规队（只统计三技能）
    格式三: #干员记录 <干员A>+<干员B>+... <流派>
      示例: #干员记录 羽毛笔+银灰 无精英满级

    组合查询限定在某个流派上，team.members 为 AND（同时上场）关系；
    每个成员可带技能号，不带则匹配该干员的任意技能。
    """
    args = match.group(1).strip()

    if not args:
        return (
            "缺少参数，格式：#干员记录 <干员> <流派>\n"
            "或：#干员记录 <干员A>+<干员B> <流派> 查组合记录\n"
            "指定技能：#干员记录 银灰3 常规队\n"
            "示例：#干员记录 羽毛笔 无精英满级"
        )

    # 最后一个空格分隔「干员部分」和「流派」（兼容带空格的英文名如 "La Pluma"）
    parts = args.rsplit(maxsplit=1)
    if len(parts) < 2:
        return (
            "缺少流派参数，格式：#干员记录 <干员> <流派>\n"
            "示例：#干员记录 羽毛笔 无精英满级\n"
            "组合：#干员记录 羽毛笔+银灰 无精英满级\n"
            "指定技能：#干员记录 银灰3 常规队"
        )

    operator_part = parts[0].strip()
    category_input = parts[1].strip()

    # 干员部分含 + 号 → 组合查询（team.members 多干员 AND）
    if "+" in operator_part:
        tokens = _parse_combo(operator_part)
        if len(tokens) < 2:
            return (
                "组合查询至少需要两个干员，格式：#干员记录 <干员A>+<干员B> <流派>\n"
                "示例：#干员记录 羽毛笔+银灰 无精英满级\n"
                "可分别指定技能：#干员记录 羽毛笔1+银灰3 无精英满级"
            )
        if len(tokens) > MAX_COMBO_OPERATORS:
            return f"最多支持 {MAX_COMBO_OPERATORS} 个干员的组合查询"
        is_combo = True
    else:
        # 干员名误填成了流派名/别名（参数写反）时给出友好提示
        if operator_part in CATEGORIES or operator_part in CATEGORY_ALIASES:
            return (
                f"「{operator_part}」是流派名，不是干员哦～\n"
                f"格式：#干员记录 <干员> <流派>\n"
                f"示例：#干员记录 羽毛笔 无精英满级"
            )
        tokens = [operator_part]
        is_combo = False

    # 解析技能号：银灰3 → ("银灰", "3")
    parsed = []
    for token in tokens:
        name, skill = _split_operator_skill(token)
        parsed.append({"token": token, "name": name, "skill": skill})

    category = normalize_category(category_input)
    if not category:
        return f"未找到流派 \"{category_input}\"，发送 #流派 查看所有流派"

    def make_conditions() -> list[dict]:
        return [
            {"field": "team", "value": {"members": _build_members(parsed)}},
            {"field": "category", "value": category},
        ]

    logger.info(
        "#干员记录: operators=%s, category=%s, combo=%s",
        [(it["name"], it["skill"]) for it in parsed],
        category,
        is_combo,
    )

    result, error = await _search_records(make_conditions())

    # 1 星小车（Castle-3 / Lancet-2）这类名字本身以数字结尾：拆错了就回退成
    # 完整干员名再查一次。它们本来就没有技能，所以回退不会丢失合法筛选。
    if error and any(it["skill"] for it in parsed):
        bad = _extract_unrecognized_name(error)
        reverted = False
        for it in parsed:
            if not it["skill"]:
                continue
            if bad is None or it["name"] == bad:
                it["name"], it["skill"] = it["token"], None
                reverted = True
        if reverted:
            logger.info("#干员记录: 技能号回退后重试 %s", [it["name"] for it in parsed])
            result, error = await _search_records(make_conditions())

    if error:
        return error

    count_valid = result.count_valid
    count = result.count

    if count_valid == 0:
        if is_combo:
            return f"「{_display(parsed)}」在「{category}」没有找到同时上场的记录"
        return f"「{_display(parsed)}」在「{category}」没有找到记录"

    old_count = count - count_valid

    # 合约记录单独统计（危机合约 + 危机合约Re，因合约非常驻）
    # 合约记录仅统计有效合约记录，合约旧纪录计入旧纪录行
    contract_count = 0
    contract_failed = False
    for story_name in ("危机合约", "危机合约Re"):
        c_result, c_error = await _search_records(
            make_conditions() + [{"field": "story", "value": story_name}]
        )
        if c_error is None:
            contract_count += c_result.count_valid
        else:
            # 不能静默当成 0：否则失败部分会被算进「有效记录」，
            # 四行数字不再满足 总记录 = 有效 + 合约 + 旧纪录，且用户看不出来
            logger.warning("合约记录查询失败(%s): %s", story_name, c_error)
            contract_failed = True

    # 有效记录 = 非合约的有效记录（合约有效已单独列为合约记录）
    effective_count = count_valid - contract_count

    label = "同时上场的记录统计" if is_combo else "记录统计"
    if contract_failed:
        # 合约统计不可用时，不给出会误导的「有效/合约」拆分
        tail = (
            "有效记录：统计不可用（合约记录查询失败）\n"
            f"旧纪录：{old_count} 条\n"
            "⚠️ 合约记录统计暂时不可用，请稍后重试"
        )
    else:
        tail = (
            f"有效记录：{effective_count} 条\n"
            f"合约记录：{contract_count} 条\n"
            f"旧纪录：{old_count} 条"
        )
    return (
        f"「{_display(parsed)}」在「{category}」的{label}：\n"
        f"总记录：{count} 条\n"
        f"{tail}"
    )
