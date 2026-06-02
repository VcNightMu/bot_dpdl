"""formatter/uncleared.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from formatter.uncleared import format_uncleared


class TestFormatUncleared:
    def test_empty_uncleared(self):
        result = format_uncleared("惊霆无声", "四星队", [])
        assert "已通关" in result
        assert "🎉" in result

    def test_basic_format(self):
        uncleared = [
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal"},
        ]
        result = format_uncleared("惊霆无声", "四星队", uncleared)
        assert "惊霆无声" in result
        assert "四星队" in result
        assert "H11-1" in result
        assert "1个" in result

    def test_multiple_uncleared(self):
        uncleared = [
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal"},
            {"operation": "H11-2", "cn_name": "惊霆行动-2", "difficulty": "challenge"},
        ]
        result = format_uncleared("惊霆无声", "四星队", uncleared)
        assert "2个" in result

    def test_challenge_label_with_index(self):
        """有 operation_index 且 has_challenge=True 时显示难度标签"""
        uncleared = [
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge"},
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal"},
        ]
        op_index = {"by_operation": {"H11-1": {"has_challenge": True}}}
        result = format_uncleared("惊霆无声", "四星队", uncleared, op_index)
        assert "[突袭]" in result
        assert "[普通]" in result

    def test_no_label_when_no_challenge(self):
        """has_challenge=False 时不显示标签"""
        uncleared = [
            {"operation": "GT-1", "cn_name": "打磨利刃", "difficulty": "normal"},
        ]
        op_index = {"by_operation": {"GT-1": {"has_challenge": False}}}
        result = format_uncleared("行动", "四星队", uncleared, op_index)
        assert "[普通]" not in result
        assert "[突袭]" not in result

    def test_no_index_no_labels(self):
        """不传 operation_index 时不显示标签"""
        uncleared = [
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge"},
        ]
        result = format_uncleared("惊霆无声", "四星队", uncleared)
        assert "[突袭]" not in result

    def test_missing_cn_name(self):
        uncleared = [
            {"operation": "GT-1", "difficulty": "normal"},
        ]
        result = format_uncleared("行动", "四星队", uncleared)
        assert "GT-1" in result

    def test_is_string(self):
        result = format_uncleared("ep", "cat", [])
        assert isinstance(result, str)

    def test_only_challenge_received_shows_tag(self):
        """只收到challenge时，正常展示带突袭标签"""
        uncleared = [
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge"},
        ]
        op_index = {"by_operation": {"H11-1": {"has_challenge": True}}}
        result = format_uncleared("惊霆无声", "四星队", uncleared, op_index)
        assert "[突袭]" in result
        assert "[普通]" not in result
        assert "1个" in result

    def test_only_normal_received_no_tag(self):
        """只收到normal时，显示普通标签"""
        uncleared = [
            {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal"},
        ]
        op_index = {"by_operation": {"H11-1": {"has_challenge": True}}}
        result = format_uncleared("惊霆无声", "四星队", uncleared, op_index)
        assert "[突袭]" not in result
        assert "[普通]" in result
        assert "1个" in result
