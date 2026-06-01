"""resolver/operation.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from resolver.operation import normalize_operation, resolve_operation, build_operation_index


class TestNormalizeOperation:
    """normalize_operation 归一化测试"""

    def test_uppercase_passthrough(self):
        assert normalize_operation("M8-8") == "M8-8"

    def test_lowercase_to_upper(self):
        assert normalize_operation("m8-8") == "M8-8"

    def test_mixed_case(self):
        assert normalize_operation("h11-1") == "H11-1"

    def test_space_to_hyphen(self):
        assert normalize_operation("M8 8") == "M8-8"

    def test_complex_spacing(self):
        assert normalize_operation("gt ex1") == "GT-EX-1"

    def test_already_normalized(self):
        assert normalize_operation("GT-EX-1") == "GT-EX-1"

    def test_empty_string(self):
        assert normalize_operation("") == ""

    def test_whitespace_only(self):
        assert normalize_operation("   ") == ""

    def test_single_letter(self):
        assert normalize_operation("a") == "A"

    def test_single_digit(self):
        assert normalize_operation("1") == "1"

    def test_only_digits(self):
        assert normalize_operation("123") == "123"

    def test_hyphen_only(self):
        assert normalize_operation("-") == "-"

    def test_trailing_spaces(self):
        assert normalize_operation("  M8-8  ") == "M8-8"

    def test_multiple_spaces(self):
        assert normalize_operation("M8   8") == "M8-8"

    def test_special_chars_preserved(self):
        assert normalize_operation("A-B") == "A-B"

    def test_letter_digit_letter(self):
        """字母-数字-字母：字母→数字和数字→字母处都插入"""
        assert normalize_operation("AB1C") == "AB-1-C"


class TestBuildOperationIndex:
    """build_operation_index 索引构建测试"""

    SAMPLE_MENU = [
        {
            "story": "活动关卡",
            "episodes": [
                {
                    "episode": "惊霆无声",
                    "operations": [
                        {"operation": "H11-1", "cn_name": "惊霆行动-1", "hasChallenge": True},
                        {"operation": "H11-2", "cn_name": "惊霆行动-2", "hasChallenge": False},
                    ],
                }
            ],
        },
        {
            "story": "主线关卡",
            "episodes": [
                {
                    "episode": "破碎日冕",
                    "operations": [
                        {"operation": "M8-8", "cn_name": "破碎", "hasChallenge": True},
                    ],
                }
            ],
        },
    ]

    def test_by_operation_index(self):
        idx = build_operation_index(self.SAMPLE_MENU)
        assert "H11-1" in idx["by_operation"]
        assert idx["by_operation"]["H11-1"]["episode"] == "惊霆无声"
        assert idx["by_operation"]["H11-1"]["has_challenge"] is True

    def test_by_cn_name_index(self):
        idx = build_operation_index(self.SAMPLE_MENU)
        assert "惊霆行动-1" in idx["by_cn_name"]
        assert idx["by_cn_name"]["惊霆行动-1"]["operation"] == "H11-1"

    def test_multiple_stories(self):
        idx = build_operation_index(self.SAMPLE_MENU)
        assert len(idx["by_operation"]) == 3

    def test_empty_menu(self):
        idx = build_operation_index([])
        assert idx["by_operation"] == {}
        assert idx["by_cn_name"] == {}

    def test_no_challenge(self):
        idx = build_operation_index(self.SAMPLE_MENU)
        assert idx["by_operation"]["H11-2"]["has_challenge"] is False


class TestResolveOperation:
    """resolve_operation 精确匹配测试"""

    INDEX = {
        "by_operation": {
            "M8-8": {"operation": "M8-8", "cn_name": "破碎", "episode": "破碎日冕", "has_challenge": True},
            "H11-1": {"operation": "H11-1", "cn_name": "惊霆行动-1", "episode": "惊霆无声", "has_challenge": True},
        },
        "by_cn_name": {
            "破碎": {"operation": "M8-8", "cn_name": "破碎", "episode": "破碎日冕", "has_challenge": True},
            "惊霆行动-1": {"operation": "H11-1", "cn_name": "惊霆行动-1", "episode": "惊霆无声", "has_challenge": True},
        },
    }

    def test_match_by_operation(self):
        result = resolve_operation("M8-8", self.INDEX)
        assert result is not None
        info, method = result
        assert info["operation"] == "M8-8"
        assert method == "operation"

    def test_match_by_operation_case_insensitive(self):
        result = resolve_operation("m8-8", self.INDEX)
        assert result is not None
        assert result[0]["operation"] == "M8-8"

    def test_match_by_cn_name(self):
        result = resolve_operation("惊霆行动-1", self.INDEX)
        assert result is not None
        info, method = result
        assert info["cn_name"] == "惊霆行动-1"
        assert method == "cn_name"

    def test_no_match(self):
        assert resolve_operation("不存在", self.INDEX) is None

    def test_empty_input(self):
        assert resolve_operation("", self.INDEX) is None

    def test_whitespace_input(self):
        assert resolve_operation("   ", self.INDEX) is None

    def test_partial_match_rejected(self):
        """不支持模糊匹配"""
        assert resolve_operation("H11", self.INDEX) is None

    def test_operation_priority_over_cn_name(self):
        """operation 匹配优先于 cn_name"""
        idx = {
            "by_operation": {"X-1": {"operation": "X-1", "cn_name": "同名"}},
            "by_cn_name": {"同名": {"operation": "Y-2", "cn_name": "同名"}},
        }
        result = resolve_operation("X-1", idx)
        assert result[0]["operation"] == "X-1"
