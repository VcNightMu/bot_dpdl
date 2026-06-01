"""api_client/models.py 单元测试。"""

import sys
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "api_client.models", Path(r"F:\ArkCodes\bot_dpdl\api_client\models.py")
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["api_client.models"] = _mod
_spec.loader.exec_module(_mod)

from api_client.models import (
    BotRecord,
    MenuEpisode,
    MenuOperation,
    MenuStory,
    QueryResult,
    StaleResult,
    UnclearedResult,
)


class TestBotRecord:
    def test_defaults(self):
        r = BotRecord()
        assert r.id == ""
        assert r.raider == ""
        assert r.operation_type == "normal"
        assert r.team == []
        assert r.category == []
        assert r.group == ""
        assert r.is_recommended is False

    def test_from_dict_snake_case(self):
        data = {
            "id": "abc123",
            "raider": "玩家A",
            "url": "https://bilibili.com/video/BV1test",
            "date_published": "2024-09-01",
            "story": "活动关卡",
            "episode": "惊霆无声",
            "operation": "H11-1",
            "cn_name": "惊霆行动-1",
            "operationType": "challenge",
            "team": [{"name": "司霆惊蛰", "skillStr": "1"}],
            "category": ["四星队"],
            "group": "旧纪录",
            "isRecommended": True,
            "remark1": "备注",
        }
        r = BotRecord.from_dict(data)
        assert r.id == "abc123"
        assert r.raider == "玩家A"
        assert r.date_published == "2024-09-01"
        assert r.cn_name == "惊霆行动-1"
        assert r.operation_type == "challenge"
        assert len(r.team) == 1
        assert r.team[0]["name"] == "司霆惊蛰"
        assert r.category == ["四星队"]
        assert r.group == "旧纪录"
        assert r.is_recommended is True

    def test_from_dict_camel_case(self):
        data = {
            "id": "x",
            "datePublished": "2024-01-01",
            "cnName": "测试关",
            "operationType": "normal",
        }
        r = BotRecord.from_dict(data)
        assert r.date_published == "2024-01-01"
        assert r.cn_name == "测试关"

    def test_from_dict_empty(self):
        r = BotRecord.from_dict({})
        assert r.id == ""
        assert r.operation_type == "normal"
        assert r.team == []


class TestQueryResult:
    def test_from_dict(self):
        data = {
            "count": 10,
            "countValid": 8,
            "records": [
                {"id": "r1", "raider": "A", "operation": "M8-8"},
                {"id": "r2", "raider": "B", "operation": "M8-8"},
            ],
        }
        qr = QueryResult.from_dict(data)
        assert qr.count == 10
        assert qr.count_valid == 8
        assert len(qr.records) == 2
        assert qr.records[0].id == "r1"
        assert qr.records[1].raider == "B"

    def test_from_dict_empty(self):
        qr = QueryResult.from_dict({})
        assert qr.count == 0
        assert qr.count_valid == 0
        assert qr.records == []

    def test_count_valid_defaults_to_len(self):
        data = {"records": [{"id": "a"}, {"id": "b"}]}
        qr = QueryResult.from_dict(data)
        assert qr.count_valid == 2


class TestUnclearedResult:
    def test_from_dict(self):
        data = {
            "episode": "惊霆无声",
            "category": "四星队",
            "uncleared": [
                {"operation": "H11-1", "difficulty": "challenge"},
            ],
        }
        ur = UnclearedResult.from_dict(data)
        assert ur.episode == "惊霆无声"
        assert ur.category == "四星队"
        assert len(ur.uncleared) == 1
        assert ur.uncleared[0]["operation"] == "H11-1"

    def test_from_dict_empty(self):
        ur = UnclearedResult.from_dict({})
        assert ur.episode == ""
        assert ur.uncleared == []


class TestStaleResult:
    def test_from_dict(self):
        data = {
            "episode": "惊霆无声",
            "category": "四星队",
            "days": 180,
            "stale": [
                {"operation": "H11-1", "ageDays": 400},
            ],
        }
        sr = StaleResult.from_dict(data)
        assert sr.episode == "惊霆无声"
        assert sr.days == 180
        assert len(sr.stale) == 1
        assert sr.stale[0]["ageDays"] == 400

    def test_from_dict_defaults(self):
        sr = StaleResult.from_dict({})
        assert sr.days == 365
        assert sr.stale == []


class TestMenuOperation:
    def test_from_dict(self):
        data = {"operation": "GT-1", "cn_name": "日正当中", "hasChallenge": False}
        mo = MenuOperation.from_dict(data)
        assert mo.operation == "GT-1"
        assert mo.cn_name == "日正当中"
        assert mo.has_challenge is False

    def test_from_dict_challenge(self):
        mo = MenuOperation.from_dict({"operation": "H11-1", "hasChallenge": True})
        assert mo.has_challenge is True


class TestMenuEpisode:
    def test_from_dict(self):
        data = {
            "episode": "骑兵与猎人",
            "operations": [
                {"operation": "GT-1", "cn_name": "日正当中"},
                {"operation": "GT-2", "cn_name": "沙场血路"},
            ],
        }
        me = MenuEpisode.from_dict(data)
        assert me.episode == "骑兵与猎人"
        assert len(me.operations) == 2
        assert me.operations[0].operation == "GT-1"

    def test_from_dict_empty_operations(self):
        me = MenuEpisode.from_dict({"episode": "X"})
        assert me.operations == []


class TestMenuStory:
    def test_from_dict(self):
        data = {
            "story": "活动关卡",
            "episodes": [
                {
                    "episode": "惊霆无声",
                    "operations": [{"operation": "H11-1", "cn_name": "惊霆行动-1"}],
                }
            ],
        }
        ms = MenuStory.from_dict(data)
        assert ms.story == "活动关卡"
        assert len(ms.episodes) == 1
        assert ms.episodes[0].episode == "惊霆无声"
        assert ms.episodes[0].operations[0].operation == "H11-1"

    def test_from_dict_nested_empty(self):
        ms = MenuStory.from_dict({})
        assert ms.story == ""
        assert ms.episodes == []
