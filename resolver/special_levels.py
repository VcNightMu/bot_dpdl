# 日期: 2026-11-17
# 开发者: 橘雪莉
# 功能摘要: 特殊关卡清单 —— 机制性不可达/非正常通关的关卡与活动，bot 指令与排查报表共用
# 模型: deepseek-flash

"""特殊关卡清单。

有些关卡在「练度限制流派」（无精英满级、四星队等）下**客观上无法参与**，
或本身就不是正常通关，因此不应被算作「待攻克」：

1. **固定编队 / 固定干员**：干员由关卡给定，无法自选练度与编成
2. **剧情演绎图**：无战斗，任何流派都没有记录
3. **特殊 0 人地图**：常规队可无需干员通关，最优解即 0 人
4. **按活动整体排除**：非正常可攻克的活动（多队编成、特殊规则等）

## 为什么要在项目内自己维护

wiki 侧 `/bot/uncleared` 有一份**人工维护**的排除名单，但更新滞后：
例如 `阴云火花` 的 TB-9/TB-10、`沃伦姆德的薄暮` 的 TW-S-1/S-2 已被排除，
而 `揭幕者们` 的 PV-SP-1/2/3 仍会被当作「未通关」返回。
wiki 管理员较忙，短期内靠本项目自行兜底。

**这份清单只能人工维护** —— wiki 数据里没有可靠字段能自动识别这些关卡
（`hasChallenge` 只表示有无突袭，不表示能否自选干员）。

## 怎么维护

发现新的特殊关卡时，把**关卡代号**加进对应的集合即可；
新增非正常可攻克的活动，把**活动名**加进 `EXCLUDED_EPISODES`。
bot 指令与排查报表会自动同步。
"""
from __future__ import annotations

# ---- 固定编队 / 固定干员：干员由关卡给定 ----
FIXED_FORMATION_LEVELS: frozenset[str] = frozenset({
    # 活动
    "TB-9", "TB-10",          # 阴云火花 白房子酒吧 / 半价古董店
    "AW-S-1", "AW-S-2",       # 日暮寻路 入鞘 / 行路
    "BW-S-1",                 # 好久不见 保卫阿根
    "DC-S-1", "DC-S-2",       # 春分 水悠悠 / 路迢迢
    "FD-S-1", "FD-S-2",       # 眠于树影之中 冻土疆界 / 非自然知觉
    "TG-S-1", "TG-S-2",       # 去咧嘴谷 穿洞绳操作指南 / 升罐笼注意事项
    "KR-S-1", "KR-S-2",       # 熔炉“还魂”记 卡兹戴尔：温饱之后 / 精神建设
    "SE-S-1", "SE-S-2",       # 我们明日见 金铁失格 / 血肉失控
    "FM-S-1", "FM-S-2",       # 镜中集 有求则苦 / 莫向外求
    "PV-SP-1", "PV-SP-2", "PV-SP-3",  # 揭幕者们 试演/即兴/狂欢之夜烟花秀
    # 主线
    "1-11", "1-2",            # 黑暗时代·下
    "6-7",                    # 苦难摇篮 断弦
    "11-17",                  # 淬火尘霾
    "16-18",                  # 反常光谱
    "17-16",                  # 相变临界
})

# ---- 剧情演绎图：无战斗 ----
NARRATIVE_LEVELS: frozenset[str] = frozenset({
    "6-17",     # 苦难摇篮 冬逝
    "JT8-1",    # 怒号光明 恨火，流向原野
    "11-19",    # 淬火尘霾
    "14-10",    # 慈悲灯塔
    "14-22",    # 慈悲灯塔
    "15-2",     # 离解复合
    "15-19",    # 离解复合
    "16-9",     # 反常光谱
})

# ---- 特殊 0 人地图：常规队可无需干员通关 ----
ZERO_OPERATOR_LEVELS: frozenset[str] = frozenset({
    "7-12",     # 苦难摇篮 浸染-2
})

# ---- 只有「突袭」是固定干员的关卡 ----
# 普通仍可正常打，仅突袭槽位对练度限制流派不适用。
# 仅统计口径需要（报表算「关卡×难度」时排除突袭槽位）；
# bot 侧无需特殊处理——wiki 的 uncleared 已不返回这些关卡。
CHALLENGE_ONLY_FIXED: frozenset[str] = frozenset({
    "TW-S-1", "TW-S-2",   # 沃伦姆德的薄暮 三座巨像 / 一束哀悼
})

# ---- 整块排除的活动：非正常可攻克 ----
EXCLUDED_EPISODES: frozenset[str] = frozenset({
    "纷争演绎",    # 多队编成的特殊玩法
    "荷谟伊智境",  # 特殊规则活动
})

# 上述「整关排除」关卡的并集
EXCLUDED_LEVELS: frozenset[str] = (
    FIXED_FORMATION_LEVELS | NARRATIVE_LEVELS | ZERO_OPERATOR_LEVELS
)


def normalize_operation(operation: str) -> str:
    """关卡代号归一化（大写、去空白），与清单里的写法对齐。"""
    return (operation or "").strip().upper()


def is_excluded_level(operation: str) -> bool:
    """该关卡是否属于「机制性不可达」，不应计入待攻克。"""
    return normalize_operation(operation) in EXCLUDED_LEVELS


def is_challenge_only_fixed(operation: str) -> bool:
    """该关卡是否「仅突袭」为固定干员（普通仍可打）。"""
    return normalize_operation(operation) in CHALLENGE_ONLY_FIXED


def is_excluded_episode(episode: str) -> bool:
    """该活动是否属于「非正常可攻克」，整体不纳入统计。"""
    return (episode or "").strip() in EXCLUDED_EPISODES
