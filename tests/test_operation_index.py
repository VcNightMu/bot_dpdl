"""cache/operation_index.py 单元测试。"""

import sys
import types
import importlib.util
from pathlib import Path

import pytest

_root = Path(r"F:\ArkCodes\bot_dpdl")

def _make_pkg(name: str, path: Path) -> types.ModuleType:
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__path__ = [str(path)]
        sys.modules[name] = m
    return sys.modules[name]

_bot = _make_pkg("bot_dpdl", _root)
_api_pkg = _make_pkg("api_client", _root / "api_client")
_bot.api_client = _api_pkg

_spec_m = importlib.util.spec_from_file_location("api_client.models", _root / "api_client/models.py")
_mod_m = importlib.util.module_from_spec(_spec_m)
sys.modules["api_client.models"] = _mod_m
_spec_m.loader.exec_module(_mod_m)

_cache_pkg = _make_pkg("cache", _root / "cache")
_bot.cache = _cache_pkg

_spec = importlib.util.spec_from_file_location("cache.operation_index", _root / "cache/operation_index.py")
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = "bot_dpdl.cache"
sys.modules["cache.operation_index"] = _mod
_spec.loader.exec_module(_mod)

from api_client.models import MenuEpisode, MenuOperation, MenuStory
from cache.operation_index import OperationIndex, normalize_operation


def _make_stories():
    return [
        MenuStory(
            story="活动关卡",
            episodes=[
                MenuEpisode(
                    episode="惊霆无声",
                    operations=[
                        MenuOperation(operation="H11-1", cn_name="惊霆行动-1", has_challenge=True),
                        MenuOperation(operation="H11-2", cn_name="惊霆行动-2", has_challenge=False),
                    ],
                ),
                MenuEpisode(
                    episode="骑兵与猎人",
                    operations=[
                        MenuOperation(operation="GT-1", cn_name="日正当中", has_challenge=False),
                        MenuOperation(operation="GT-EX-1", cn_name="大地惊雷", has_challenge=True),
                    ],
                ),
            ],
        ),
        MenuStory(
            story="主线关卡",
            episodes=[
                MenuEpisode(
                    episode="破碎日冕",
                    operations=[
                        MenuOperation(operation="M8-8", cn_name="破碎日冕", has_challenge=True),
                    ],
                ),
            ],
        ),
    ]


class TestNormalizeOperation:
    def test_already_normalized(self):
        assert normalize_operation("M8-8") == "M8-8"

    def test_lowercase(self):
        assert normalize_operation("h11-1") == "H11-1"

    def test_space_to_hyphen(self):
        assert normalize_operation("M8 8") == "M8-8"

    def test_mixed_case_with_space(self):
        assert normalize_operation("gt ex1") == "GT-EX-1"

    def test_whitespace_stripped(self):
        assert normalize_operation("  H11-1  ") == "H11-1"

    def test_idempotent(self):
        s = "gt ex1"
        first = normalize_operation(s)
        second = normalize_operation(first)
        assert first == second

    def test_already_has_hyphen(self):
        assert normalize_operation("GT-EX-1") == "GT-EX-1"


class TestOperationIndex:
    def test_build(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        assert len(idx.by_operation) == 5
        assert len(idx.by_cn_name) == 5

    def test_resolve_by_operation_exact(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        entry = idx.resolve("H11-1")
        assert entry is not None
        assert entry.operation == "H11-1"
        assert entry.cn_name == "惊霆行动-1"
        assert entry.episode == "惊霆无声"
        assert entry.story == "活动关卡"
        assert entry.has_challenge is True

    def test_resolve_by_operation_case_insensitive(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        entry = idx.resolve("h11-1")
        assert entry is not None
        assert entry.operation == "H11-1"

    def test_resolve_by_cn_name(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        entry = idx.resolve("日正当中")
        assert entry is not None
        assert entry.operation == "GT-1"
        assert entry.episode == "骑兵与猎人"

    def test_resolve_not_found(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        assert idx.resolve("不存在的关卡") is None

    def test_resolve_empty_input(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        assert idx.resolve("") is None

    def test_resolve_normalized_operation(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        entry = idx.resolve("M8 8")
        assert entry is not None
        assert entry.operation == "M8-8"

    def test_get_episode_operations(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        ops = idx.get_episode_operations("惊霆无声")
        assert len(ops) == 2
        names = {op.operation for op in ops}
        assert names == {"H11-1", "H11-2"}

    def test_get_episode_operations_empty(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        ops = idx.get_episode_operations("不存在的活动")
        assert ops == []

    def test_build_clears_old_data(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        assert len(idx.by_operation) == 5

        idx.build([
            MenuStory(
                story="主线",
                episodes=[
                    MenuEpisode(
                        episode="A",
                        operations=[MenuOperation(operation="A-1", cn_name="关A")],
                    )
                ],
            )
        ])
        assert len(idx.by_operation) == 1
        assert "A-1" in idx.by_operation

    def test_multiple_stories(self):
        idx = OperationIndex()
        idx.build(_make_stories())
        assert idx.resolve("H11-1") is not None
        assert idx.resolve("M8-8") is not None
        assert idx.resolve("H11-1").story == "活动关卡"
        assert idx.resolve("M8-8").story == "主线关卡"

    def test_operation_priority_over_cn_name(self):
        stories = [
            MenuStory(
                story="测试",
                episodes=[
                    MenuEpisode(
                        episode="X",
                        operations=[
                            MenuOperation(operation="特殊名", cn_name="另一个名"),
                        ],
                    )
                ],
            )
        ]
        idx = OperationIndex()
        idx.build(stories)
        entry = idx.resolve("特殊名")
        assert entry is not None
        assert entry.operation == "特殊名"
