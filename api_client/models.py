# 日期: 2026-06-01
# 开发者: 黑部奈叶香
# 功能: 少人WIKI API响应数据模型定义，使用dataclass封装各类数据结构
# 模型: mimo/mimo-v2.5

"""少人WIKI API 响应模型。

使用 dataclass 定义 API 返回的数据结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BotRecord:
    """攻略记录"""
    id: str = ""
    raider: str = ""
    url: str = ""
    date_published: str = ""
    story: str = ""
    episode: str = ""
    operation: str = ""
    cn_name: str = ""
    operation_type: str = "normal"  # "normal" | "challenge"
    team: list[dict[str, Any]] = field(default_factory=list)
    category: list[str] = field(default_factory=list)
    group: str = ""  # "" | "旧纪录"
    is_recommended: bool = False
    remark1: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BotRecord:
        # API 返回的字段名可能是 camelCase 或 snake_case，兼容处理
        return cls(
            id=data.get("id") or data.get("_id", ""),
            raider=data.get("raider", ""),
            url=data.get("url", ""),
            date_published=data.get("datePublished") or data.get("date_published", ""),
            story=data.get("story", ""),
            episode=data.get("episode", ""),
            operation=data.get("operation", ""),
            cn_name=data.get("cnName") or data.get("cn_name", ""),
            operation_type=data.get("operationType", "normal"),
            team=data.get("team", []),
            category=data.get("category", []),
            group=data.get("group", ""),
            is_recommended=data.get("isRecommended", False),
            remark1=data.get("remark1", ""),
        )


@dataclass
class QueryResult:
    """查询结果"""
    count: int = 0
    count_valid: int = 0
    records: list[BotRecord] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryResult:
        records = [BotRecord.from_dict(r) for r in data.get("records", [])]
        return cls(
            count=data.get("count", 0),
            count_valid=data.get("countValid", len(records)),
            records=records,
        )


@dataclass
class UnclearedResult:
    """未通关结果"""
    episode: str = ""
    category: str = ""
    uncleared: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnclearedResult:
        return cls(
            episode=data.get("episode", ""),
            category=data.get("category", ""),
            uncleared=data.get("uncleared", []),
        )


@dataclass
class StaleResult:
    """待压人结果"""
    episode: str = ""
    category: str = ""
    days: int = 365
    stale: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StaleResult:
        return cls(
            episode=data.get("episode", ""),
            category=data.get("category", ""),
            days=data.get("days", 365),
            stale=data.get("stale", []),
        )


@dataclass
class MenuOperation:
    """关卡节点"""
    operation: str = ""
    cn_name: str = ""
    has_challenge: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MenuOperation:
        return cls(
            operation=data.get("operation", ""),
            cn_name=data.get("cn_name", ""),
            has_challenge=data.get("hasChallenge", False),
        )


@dataclass
class MenuEpisode:
    """活动节点"""
    episode: str = ""
    operations: list[MenuOperation] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MenuEpisode:
        operations = [MenuOperation.from_dict(o) for o in data.get("operations", [])]
        return cls(
            episode=data.get("episode", ""),
            operations=operations,
        )


@dataclass
class MenuStory:
    """故事节点"""
    story: str = ""
    episodes: list[MenuEpisode] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MenuStory:
        episodes = [MenuEpisode.from_dict(e) for e in data.get("episodes", [])]
        return cls(
            story=data.get("story", ""),
            episodes=episodes,
        )
