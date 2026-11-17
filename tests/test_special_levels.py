# 日期: 2026-11-17
# 开发者: 橘雪莉
# 功能: 特殊关卡清单与 #未通关 过滤逻辑的单元测试
# 模型: deepseek-flash


import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""特殊关卡清单 / #未通关 过滤 单元测试"""

import re
import pytest

from resolver.special_levels import (
    CHALLENGE_ONLY_FIXED,
    EXCLUDED_EPISODES,
    EXCLUDED_LEVELS,
    FIXED_FORMATION_LEVELS,
    NARRATIVE_LEVELS,
    ZERO_OPERATOR_LEVELS,
    is_challenge_only_fixed,
    is_excluded_episode,
    is_excluded_level,
    normalize_operation,
)
from qq_bot.commands.uncleared import filter_uncleared, handle_uncleared


class TestSpecialLevelSets:
    def test_sets_are_upper_case(self):
        """清单里的代号统一大写，避免大小写不一致导致漏判。"""
        for s in (FIXED_FORMATION_LEVELS, NARRATIVE_LEVELS,
                  ZERO_OPERATOR_LEVELS, CHALLENGE_ONLY_FIXED):
            for op in s:
                assert op == op.upper(), f"{op} 不是大写"

    def test_excluded_levels_is_union(self):
        assert EXCLUDED_LEVELS == (FIXED_FORMATION_LEVELS
                                   | NARRATIVE_LEVELS
                                   | ZERO_OPERATOR_LEVELS)

    def test_challenge_only_not_in_excluded_levels(self):
        """仅突袭不适用的关卡，普通仍可打，不应整关排除。"""
        assert not (CHALLENGE_ONLY_FIXED & EXCLUDED_LEVELS)

    def test_known_fixed_formation_levels(self):
        for op in ("TB-9", "TB-10", "PV-SP-1", "PV-SP-2", "PV-SP-3",
                   "1-11", "1-2", "6-7", "11-17", "16-18", "17-16"):
            assert is_excluded_level(op), op

    def test_known_narrative_levels(self):
        for op in ("6-17", "JT8-1", "11-19", "14-10", "14-22",
                   "15-2", "15-19", "16-9"):
            assert is_excluded_level(op), op

    def test_zero_operator_level(self):
        assert is_excluded_level("7-12")

    def test_normal_level_not_excluded(self):
        for op in ("PV-1", "PV-EX-8", "H12-1", "7-11", "6-3"):
            assert not is_excluded_level(op), op

    def test_normalization(self):
        assert normalize_operation("  pv-sp-1  ") == "PV-SP-1"
        assert is_excluded_level("pv-sp-1")
        assert is_excluded_level(" PV-SP-1 ")

    def test_empty_input(self):
        assert not is_excluded_level("")
        assert not is_excluded_level(None)
        assert not is_excluded_episode("")

    def test_challenge_only_fixed(self):
        assert is_challenge_only_fixed("TW-S-1")
        assert is_challenge_only_fixed("tw-s-2")
        assert not is_challenge_only_fixed("TW-8")

    def test_excluded_episodes(self):
        assert is_excluded_episode("纷争演绎")
        assert is_excluded_episode("荷谟伊智境")
        assert not is_excluded_episode("揭幕者们")
        assert EXCLUDED_EPISODES == {"纷争演绎", "荷谟伊智境"}


class TestFilterUnclearedSpecialLevels:
    def test_drops_special_levels(self):
        items = [
            {"operation": "PV-4", "difficulty": "normal"},
            {"operation": "PV-SP-1", "difficulty": "normal"},
            {"operation": "PV-SP-2", "difficulty": "normal"},
            {"operation": "PV-SP-3", "difficulty": "normal"},
        ]
        out = filter_uncleared(items, None)
        assert [x["operation"] for x in out] == ["PV-4"]

    def test_drops_case_insensitively(self):
        items = [{"operation": "pv-sp-1", "difficulty": "normal"},
                 {"operation": "PV-1", "difficulty": "normal"}]
        out = filter_uncleared(items, None)
        assert [x["operation"] for x in out] == ["PV-1"]

    def test_all_special_returns_empty(self):
        items = [{"operation": "PV-SP-1", "difficulty": "normal"},
                 {"operation": "PV-SP-2", "difficulty": "normal"}]
        assert filter_uncleared(items, None) == []

    def test_challenge_equivalence_still_works(self):
        """剔除特殊关卡后，突袭等效普通的规则照常生效。"""
        idx = {"by_operation": {"PV-EX-2": {"has_challenge": True}}}
        items = [{"operation": "PV-EX-2", "difficulty": "normal"},
                 {"operation": "PV-SP-1", "difficulty": "normal"}]
        assert filter_uncleared(items, idx) == []

    def test_challenge_kept_when_only_challenge(self):
        idx = {"by_operation": {"PV-EX-2": {"has_challenge": True}}}
        items = [{"operation": "PV-EX-2", "difficulty": "challenge"}]
        assert len(filter_uncleared(items, idx)) == 1

    def test_does_not_touch_normal_levels(self):
        items = [{"operation": "PV-4", "difficulty": "normal"},
                 {"operation": "PV-10", "difficulty": "normal"}]
        assert len(filter_uncleared(items, None)) == 2


class TestHandleUnclearedExcludedEpisode:
    @pytest.mark.asyncio
    async def test_excluded_episode_message(self):
        match = re.match(r"^#未通关\s+(.+)", "#未通关 纷争演绎 无精英满级")
        out = await handle_uncleared(match, group_id=1, user_id=1)
        assert "特殊玩法" in out or "不" in out
        assert "未通关" in out

    @pytest.mark.asyncio
    async def test_excluded_episode_no_api_needed(self):
        """整块排除的活动应在调用 API 之前就返回，不产生网络请求。"""
        from unittest.mock import patch
        match = re.match(r"^#未通关\s+(.+)", "#未通关 荷谟伊智境 无精英满级")
        with patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            out = await handle_uncleared(match, group_id=1, user_id=1)
            MockClient.assert_not_called()
        assert "特殊玩法" in out
