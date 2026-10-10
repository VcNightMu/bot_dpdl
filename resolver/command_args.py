# 日期: 2026-06-16
# 开发者: 橘雪莉
# 功能摘要: #未通关/#待压人 共用的「活动名 + 流派 [+ 天数]」参数解析（支持含空格的活动名）
# 模型：deepseek-v4-pro

"""#未通关 / #待压人 的参数解析。

这两个指令的输入是「活动名 + 流派 [+ 天数]」三段，且都用空格分隔，
但空格是歧义分隔符——线上确实存在含空格的活动名：

    矢量突破#3 拟生态
    矢量突破#2 巫术之夜

因此不能简单 `parts[0] / parts[1]`（会截断活动名），也不能简单
`rsplit(maxsplit=1)`（会把活动名的尾词当成流派）。这里的策略是：

1. 先把「最后一个 token」当流派试一下（覆盖含空格活动名，也覆盖常规输入）
2. 不成再试「第二个 token」（保持原有的常规解析行为）
3. 都不行则报错，并明确指出多余参数放在哪里——绝不静默丢弃

天数参数同理：在流派之外的 token 里找纯数字（允许 "180天" 这种写法），
让用户写 `180 天` 也不会得到奇怪的报错。
"""
from __future__ import annotations

import re
from typing import NamedTuple

from .category import normalize_category

# 天数 token：纯数字，或数字 + 「天」
_DAYS_RE = re.compile(r"^(\d+)\s*天?$")


class CommandArgs(NamedTuple):
    """解析结果：成功时 error 为 None，失败时 episode/category 为 None。"""

    episode: str | None
    category: str | None
    days: int | None
    error: str | None


def parse_episode_category(
    args: str,
    usage: str,
    *,
    allow_days: bool = False,
) -> CommandArgs:
    """解析「活动名 + 流派 [+ 天数]」。

    args: 指令参数原文（已 strip）
    usage: 用于报错的用法提示，如 "#未通关 <活动名> <流派>"
    allow_days: 是否接受末尾的可选天数（仅 #待压人 为 True）
    """
    parts = args.split()

    if not parts:
        return CommandArgs(None, None, None, f"缺少参数，格式：{usage}")

    # -- 1. 定位流派 --
    # 语法是「活动名… 流派 [天数]」，从右往左找第一个能识别成流派的 token。
    # - 常规「惊霆无声 四星队」        → 四星队（末位，右侧无天数）
    # - 带天数「惊霆无声 四星队 180」   → 四星队（跳过数字 180）
    # - 含空格活动名「矢量突破#3 拟生态 四星队」→ 四星队
    # - 两者叠加「矢量突破#3 拟生态 四星队 180」→ 四星队
    #
    # 坑：CATEGORY_ALIASES 把练度代号也注册成了流派别名
    # （180→精一满级、1604→精一满级四星队、114→精一1级四星队 …），
    # 所以纯数字 token 既可能是天数、也可能是流派。末尾是数字时一律
    # 当天数处理并跳过，否则「#待压人 X 四星队 180」会把 180 当流派。
    category: str | None = None
    category_idx = -1

    for i in range(len(parts) - 1, -1, -1):
        tok = parts[i]
        if i == len(parts) - 1 and _DAYS_RE.match(tok):
            continue  # 末尾的纯数字是天数，不是流派
        resolved = normalize_category(tok)
        if resolved:
            category, category_idx = resolved, i
            break

    if not category:
        candidate = parts[-1] if len(parts) > 1 else parts[0]
        if len(parts) < 2:
            return CommandArgs(
                None, None, None,
                f"缺少流派参数，格式：{usage}\n发送 #流派 查看所有流派",
            )
        return CommandArgs(
            None, None, None,
            f'未找到流派 "{candidate}"，发送 #流派 查看所有流派',
        )

    # -- 2. 流派左侧 = 活动名；右侧 = 只允许天数 --
    episode_tokens = parts[:category_idx]
    trailing = parts[category_idx + 1:]

    if not episode_tokens:
        return CommandArgs(None, None, None, f"缺少活动名，格式：{usage}")

    days: int | None = None
    for j, tok in enumerate(trailing):
        m = _DAYS_RE.match(tok)
        if allow_days and j == 0 and m:
            days = int(m.group(1))
            continue
        # 流派右边只可能是天数：不是数字就是写错的天数，多半是多打的参数
        if j == 0:
            return CommandArgs(
                None, None, None,
                f"天数格式错误：{tok}，请输入数字",
            )
        return CommandArgs(
            None, None, None,
            f'活动名/流派后面的 "{tok}" 无法识别。\n'
            f"格式：{usage}\n"
            f"若活动名本身含空格（如「矢量突破#3 拟生态」），请完整输入；"
            f"多余参数请删除。",
        )

    # -- 3. 活动名多于一个 token：只有「含空格的活动名」是合法的 --
    if len(episode_tokens) > 1:
        # 逐一验证：若某个 token 单独就是流派，说明用户把顺序写反了，
        # 或活动名与流派之间混进了多余参数。
        for k, tok in enumerate(episode_tokens):
            if normalize_category(tok):
                extra = " ".join(episode_tokens[:k] + episode_tokens[k + 1:])
                return CommandArgs(
                    None, None, None,
                    f'无法确定活动名，多出的 "{extra}" 无法识别。\n'
                    f"格式：{usage}",
                )

    return CommandArgs(" ".join(episode_tokens), category, days, None)
