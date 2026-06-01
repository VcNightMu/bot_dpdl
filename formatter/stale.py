# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: #待压人指令格式化模块，过滤并展示超过N天未更新的关卡
# 模型: mimo/mimo-v2.5

"""#待压人 格式化模块

过滤规则：
- 只显示最佳记录超过N天（默认365天）未更新的关卡
- 队伍人数为1的关卡不展示

格式：
⏰ 活动名 · 流派 待压人（超过N天）

🔴 关卡代号 中文名 [突袭/普通] — X天前 | Y人
   最新记录: 日期 | 🔗 BV号
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from .video import format_video_link

# 北京时间偏移
_CST = timezone(timedelta(hours=8))


def _days_ago(date_str: str) -> int:
    """计算日期字符串距今天数"""
    try:
        # 支持多种日期格式
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(date_str, fmt).replace(tzinfo=_CST)
                delta = datetime.now(_CST) - dt
                return max(0, delta.days)
            except ValueError:
                continue
        return 0
    except Exception:
        return 0


def format_stale(
    episode: str,
    category: str,
    days: int,
    stale: list[dict[str, Any]],
) -> str:
    """格式化待压人结果

    episode: 活动名
    category: 流派名
    days: 超过天数阈值
    stale: 待压人关卡列表（API返回格式）
    """
    if not stale:
        return f"⏰ {episode} · {category} 无待压人记录（超过{days}天）"

    header = f"⏰ {episode} · {category} 待压人（超过{days}天）\n"

    lines: list[str] = []
    for item in stale:
        operation = item.get("operation", "???")
        cn_name = item.get("cn_name", "")
        difficulty = item.get("difficulty", "normal")
        age_days = item.get("ageDays", days)
        records = item.get("records", [])

        # 从 records 中提取队伍人数和最新链接
        team_size = 0
        latest_url = ""
        if records:
            # 取第一条记录的队伍人数
            first_record = records[0]
            team = first_record.get("team", [])
            team_size = len(team)
            latest_url = first_record.get("url", "")

        # 过滤：队伍人数为1的不展示
        if team_size <= 1:
            continue

        video_str = format_video_link(latest_url)

        # 难度标签
        diff_label = ""
        if difficulty == "challenge":
            diff_label = " [突袭]"
        elif difficulty == "normal":
            diff_label = " [普通]"

        # 格式化关卡名
        name_part = f"{operation} {cn_name}" if cn_name else operation

        # 第一行：🔴 关卡名 — X天前 | Y人
        line1 = f"🔴 {name_part}{diff_label} — {age_days}天前 | {team_size}人"
        # 第二行：最新记录信息
        line2 = f"   🔗 {video_str}"

        lines.append(f"{line1}\n{line2}")

    if not lines:
        return f"⏰ {episode} · {category} 无待压人记录（超过{days}天）"

    return header + "\n".join(lines)
