# 日期: 2026-10-10
# 开发者: 橘雪莉
# 功能摘要: #高难 指令的数据整理 —— 按关卡×难度取最少人，筛出 >=10 人的高难关卡
# 模型: deepseek-flash

"""#高难 的数据整理。

「高难」定义：该关卡在该流派下，**最少人记录**的队伍人数 >= 阈值（默认 10）。
即「这一关就算打到最好也得上 10 个人」，属于低配低练体系里的硬骨头。

数据来源：`POST /bot/search-records`，条件为 `category` + `episode`。
实测该端点对 `episode` 是**精确匹配**（"第八章" 返回 0，必须用 menu 里的活动名），
所以活动名的解析复用 `resolver.episode_short` 那一套。

为什么不用 `team.size` 过滤：该字段实测**只接受数字（精确匹配）**，
传 ">=10" 会被 400 拒绝，且强制要求同时给 `members` 数组。
所以"人数 >= 10"只能在本地按 `len(team)` 过滤。

⚠️ 字段名归一化：`api_client.models.BotRecord` 的 Python 字段是
`operation_type` / `cn_name`（下划线），而 API 原始 JSON 是
`operationType` / `cn_name`。**不要用 `dataclasses.asdict()` 转换**——
它输出 `operation_type` 而非 `operationType`，会让读 `operationType` 的代码
静默拿到 None，把普通与突袭合并成一组。本模块用 `_field()` 同时兼容两种形态。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, NamedTuple

# 「高难」阈值：最少人记录达到这个人数才算高难
HIGH_TEAM_THRESHOLD = 10

DIFFICULTY_LABELS: dict[str, str] = {
    "normal": "普通",
    "challenge": "突袭",
}

_MISSING = object()


def _field(rec: Any, *names: str, default: Any = None) -> Any:
    """按多个候选名取值，同时兼容 dataclass 对象与 API 原始 dict。

    候选名顺序即优先级，例如 `_field(rec, "operationType", "operation_type")`
    可同时吃下 API dict 与 BotRecord 对象。
    """
    if isinstance(rec, dict):
        for name in names:
            if name in rec:
                return rec[name]
        return default
    for name in names:
        value = getattr(rec, name, _MISSING)
        if value is not _MISSING:
            return value
    return default


def difficulty_label(
    operation: str,
    difficulty: str,
    operation_index: dict[str, Any] | None = None,
) -> str:
    """难度标签：仅当该关确实存在突袭模式时才显示。

    「突袭等效普通」相关文案（如 #未通关）依赖这个判定：没有突袭的关卡
    不该给记录打上 [普通] 标签，否则会误导。

    operation_index 为 None 时无法判断，一律不加标签。
    """
    if not operation_index:
        return ""
    info = (operation_index.get("by_operation") or {}).get(operation.upper())
    if not info or not info.get("has_challenge", False):
        return ""
    return f" [{DIFFICULTY_LABELS.get(difficulty, difficulty)}]"


class HighDifficultyRecord(NamedTuple):
    """一个命中高难的「关卡 × 难度」。"""

    operation: str
    cn_name: str
    difficulty: str                    # "normal" | "challenge"
    difficulty_label: str              # "" | " [普通]" | " [突袭]"
    min_team_size: int                 # 最少人记录的人数（>= 阈值）
    best_records: list[Any]            # 最少人规模下的全部记录，新→旧
    total_records: int                 # 该关卡×难度的记录总数
    has_challenge: bool


def find_high_difficulty(
    records: list[Any],
    *,
    threshold: int = HIGH_TEAM_THRESHOLD,
    operation_index: dict[str, Any] | None = None,
) -> list[HighDifficultyRecord]:
    """从记录列表里挑出「最少人 >= threshold」的关卡×难度。

    records: BotRecord 对象列表（或 API 原始 dict 列表，两者都支持）
    threshold: 高难阈值，默认 10
    operation_index: 关卡索引，用于判断是否有突袭模式

    返回按「最少人降序」排列的命中列表；无命中返回 []。
    """
    groups: dict[tuple[str, str], list[Any]] = defaultdict(list)

    for rec in records or []:
        operation = (_field(rec, "operation", default="") or "").strip()
        if not operation:
            continue
        team = _field(rec, "team", default=[]) or []
        if not isinstance(team, list) or not team:
            # 没有队伍的记录（异常数据）不计入人数统计，否则会被当成 0 人最优
            continue
        difficulty = (_field(rec, "operationType", "operation_type", default="normal") or "normal")
        difficulty = str(difficulty).strip() or "normal"
        groups[(operation, difficulty)].append(rec)

    hits: list[HighDifficultyRecord] = []
    for (operation, difficulty), recs in groups.items():
        best_size = min(len(_field(r, "team", default=[]) or []) for r in recs)
        if best_size < threshold:
            continue
        best_records = [r for r in recs if len(_field(r, "team", default=[]) or []) == best_size]
        info = (operation_index or {}).get("by_operation", {}).get(operation.upper())
        has_challenge = bool(info and info.get("has_challenge", False))
        hits.append(HighDifficultyRecord(
            operation=operation,
            cn_name=(_field(recs[0], "cn_name", "cnName", default="") or "").strip(),
            difficulty=difficulty,
            difficulty_label=difficulty_label(operation, difficulty, operation_index),
            min_team_size=best_size,
            best_records=best_records,
            total_records=len(recs),
            has_challenge=has_challenge,
        ))

    # 人数多的（更难的）排前面
    hits.sort(key=lambda r: (-r.min_team_size, r.operation, r.difficulty))
    return hits
