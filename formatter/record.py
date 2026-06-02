# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: #查指令记录格式化模块，处理关卡查询结果展示
# 模型: mimo/mimo-v2.5

"""#查 记录格式化模块

格式：
📋 关卡代号 中文名（突袭/普通）
🏷️ 流派 | 👤 玩家名
👥 干员列表
📅 日期 | 🔗 BV号
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from .video import format_video_link

# 北京时间偏移
_CST = timezone(timedelta(hours=8))


def _format_date(date_str: str) -> str:
    """格式化日期字符串

    支持:
    - ISO 格式: 2023-05-12T12:59:28.000Z
    - 日期格式: 2023-05-12
    - 其他: 原样返回
    """
    if not date_str:
        return "???"
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            # 转北京时间
            dt_cst = dt.astimezone(_CST)
            return dt_cst.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


# QQ单条消息建议上限（保守值）
MAX_MSG_LENGTH = 800


def _format_operator_list(team: list[dict[str, Any]]) -> str:
    """格式化干员列表

    team: [{"name": "司霆惊蛰", "skillStr": "1"}, ...]
    返回: "司霆惊蛰(1), 黑角(1), ..."
    """
    parts = []
    for op in team:
        name = op.get("name", "???")
        skill = op.get("skillStr", "?")
        parts.append(f"{name}({skill})")
    return ", ".join(parts) if parts else "无干员"


def _operation_type_label(operation_type: str) -> str:
    """operation_type → 中文标签"""
    if operation_type == "challenge":
        return "突袭"
    return "普通"


def format_single_record(record: dict[str, Any], index: int | None = None) -> str:
    """格式化单条记录

    record: BotRecord 字典
    index: 序号（多条记录时使用，从1开始）
    """
    operation = record.get("operation", "???")
    cn_name = record.get("cn_name", "???")
    op_type = _operation_type_label(record.get("operation_type", "normal"))
    category = record.get("category", ["???"])
    # category 可能是列表或字符串
    if isinstance(category, list):
        cat_str = " / ".join(category) if category else "???"
    else:
        cat_str = str(category)

    raider = record.get("raider", "???")
    team = record.get("team", [])
    date = _format_date(record.get("date_published", ""))
    url = record.get("url", "")
    video_str = format_video_link(url)

    # 第一行：📋 关卡代号 中文名（突袭/普通）
    line1 = f"📋 {operation} {cn_name}（{op_type}）"
    # 第二行：🏷️ 流派 | 👤 玩家名 | 👥 N人
    team_count = len(team)
    line2 = f"🏷️ {cat_str} | 👤 {raider} | 👥 {team_count}人"
    # 第三行：👥 干员列表
    line3 = f"👥 {_format_operator_list(team)}"
    # 第四行：📅 日期 | 🔗 BV号
    line4 = f"📅 {date} | 🔗 {video_str}"

    block = "\n".join([line1, line2, line3, line4])

    if index is not None:
        block = f"{index}️⃣ {block}"
        # 缩进后续行
        lines = block.split("\n")
        block = lines[0] + "\n" + "\n".join("   " + l for l in lines[1:])

    return block + "\n"


def format_records(records: list[dict[str, Any]], count_valid: int) -> list[str]:
    """格式化查询结果，返回消息列表（可能多条）

    records: API 返回的完整记录列表（含旧纪录）
    count_valid: API 返回的不含旧纪录的数量，可直接使用
    """
    # Feature 1: 按 group 字段过滤旧记录
    records = [r for r in records if r.get("group", "") != "旧纪录"]

    if not records:
        return ["没有找到最佳记录 😅"]

    messages: list[str] = []

    # Feature 2: 单条也显示记录人数
    header = f"共 {count_valid} 条最佳记录\n\n" if count_valid == 1 else f"找到最佳记录 {count_valid} 条\n\n"
    current_msg = header

    # Feature 3: 多条记录间插入空行
    for i, record in enumerate(records):
        text = format_single_record(record, i + 1 if count_valid > 1 else None)
        if i > 0:
            # 记录之间插入空行（不计为额外开销，用 \n\n 分隔）
            current_msg += "\n"
        if len(current_msg) + len(text) > MAX_MSG_LENGTH:
            messages.append(current_msg)
            current_msg = text
        else:
            current_msg += text
    if current_msg:
        messages.append(current_msg)

    return messages
