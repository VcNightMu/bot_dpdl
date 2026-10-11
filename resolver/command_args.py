# 日期: 2026-06-16
# 开发者: 橘雪莉
# 功能摘要: #未通关/#待压人/#高难 共用的「活动名 + 流派 [+ 数字]」参数解析（支持含空格的活动名）
# 模型：deepseek-v4-pro

"""#未通关 / #待压人 / #高难 的参数解析。

这三个指令的输入是「活动名 + 流派 [+ 数字]」三段，且都用空格分隔，
但空格是歧义分隔符——线上确实存在含空格的活动名：

    矢量突破#3 拟生态
    矢量突破#2 巫术之夜

因此不能简单 `parts[0] / parts[1]`（会截断活动名），也不能简单
`rsplit(maxsplit=1)`（会把活动名的尾词当成流派）。这里的策略是：

1. 先把「最后一个 token」当流派试一下（覆盖含空格活动名，也覆盖常规输入）
2. 不成再试「第二个 token」（保持原有的常规解析行为）
3. 都不行则报错，并明确指出多余参数放在哪里——绝不静默丢弃

末尾数字的含义由调用方决定（#待压人 = 天数，#高难 = 人数阈值），
本模块只负责取出来，不做范围校验。允许 "180天" 这种写法，
让用户写 `180 天` 也不会得到奇怪的报错。
"""
from __future__ import annotations

import re
from typing import NamedTuple

from .category import normalize_category

# 末尾数字 token：纯数字，或数字 + 「天」（兼容 #待压人 的 "180天" 写法）
_NUMBER_RE = re.compile(r"^(\d+)\s*天?$")


class CommandArgs(NamedTuple):
    """解析结果：成功时 error 为 None，失败时 episode/category 为 None。"""

    episode: str | None
    category: str | None
    value: int | None          # 末尾可选数字（#待压人=天数 / #高难=人数阈值）
    error: str | None

    @property
    def days(self) -> int | None:
        """向后兼容别名：值就是末尾数字，与 value 等价。"""
        return self.value


def parse_episode_category(
    args: str,
    usage: str,
    *,
    allow_number: bool = False,
) -> CommandArgs:
    """解析「活动名 + 流派 [+ 数字]」。

    args: 指令参数原文（已 strip）
    usage: 用于报错的用法提示，如 "#未通关 <活动名> <流派>"
    allow_number: 是否接受末尾的可选数字（#待压人 的天数 / #高难 的人数阈值）

    注意：本函数只负责把末尾数字取出来放进 `value`，
    具体取值范围（如 1–13）由调用方校验并给出针对性提示。
    """
    parts = args.split()

    if not parts:
        return CommandArgs(None, None, None, f"缺少参数，格式：{usage}")

    # -- 1. 定位流派 --
    # 语法是「活动名… 流派 [数字]」，从右往左找第一个能识别成流派的 token。
    # - 常规「惊霆无声 四星队」        → 四星队（末位，右侧无数字）
    # - 带数字「惊霆无声 四星队 180」   → 四星队（跳过数字 180）
    # - 含空格活动名「矢量突破#3 拟生态 四星队」→ 四星队
    # - 两者叠加「矢量突破#3 拟生态 四星队 180」→ 四星队
    #
    # 坑：CATEGORY_ALIASES 把练度代号也注册成了流派别名
    # （180→精一满级、1604→精一满级四星队、114→精一1级四星队 …），
    # 所以纯数字 token 既可能是末尾数字、也可能是流派。末尾是数字时一律
    # 当数字处理并跳过，否则「#待压人 X 四星队 180」会把 180 当流派。
    category: str | None = None
    category_idx = -1

    for i in range(len(parts) - 1, -1, -1):
        tok = parts[i]
        if i == len(parts) - 1 and _NUMBER_RE.match(tok):
            continue  # 末尾的纯数字是可选数字，不是流派
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

    # -- 2. 流派左侧 = 活动名；右侧 = 只允许数字 --
    episode_tokens = parts[:category_idx]
    trailing = parts[category_idx + 1:]

    if not episode_tokens:
        return CommandArgs(None, None, None, f"缺少活动名，格式：{usage}")

    value: int | None = None
    for j, tok in enumerate(trailing):
        m = _NUMBER_RE.match(tok)
        if allow_number and j == 0 and m:
            value = int(m.group(1))
            continue
        # 流派右边只可能是一个数字：不是数字，或者该指令不接受数字
        if j == 0:
            if m:
                # 是数字但本指令不支持 → 说清楚，别让用户以为格式写错了
                return CommandArgs(
                    None, None, None,
                    f"该指令不接受数字参数（收到 {tok}）。\n格式：{usage}",
                )
            return CommandArgs(
                None, None, None,
                f"末尾参数应为数字，收到：{tok}\n格式：{usage}",
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

    return CommandArgs(" ".join(episode_tokens), category, value, None)
