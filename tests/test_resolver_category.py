"""resolver/category.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from resolver.category import normalize_category, CATEGORIES, CATEGORY_ALIASES


class TestNormalizeCategory:
    """normalize_category 流派归一化测试"""

    @pytest.mark.parametrize("name", CATEGORIES)
    def test_exact_match_all_categories(self, name):
        """7个标准流派名直接匹配"""
        assert normalize_category(name) == name

    @pytest.mark.parametrize("alias,expected", [
        ("四星", "四星队"),
        ("4星", "四星队"),
        ("四星队伍", "四星队"),
        ("精一满级", "精一满级四星队"),
        ("精一满级队", "精一满级四星队"),
        ("精一满级四星", "精一满级四星队"),
        ("精一1级四星队", "精一1级四星队"),
        ("精一一级", "精一1级四星队"),
        ("精一1级队", "精一1级四星队"),
        ("精一一级队", "精一1级四星队"),
        ("三星", "三星队"),
        ("3星", "三星队"),
        ("三星队伍", "三星队"),
        ("精一", "精一1级"),
        ("精一满", "精一1级"),
        ("无精英", "无精英满级"),
        ("满级无精英", "无精英满级"),
        ("满级", "无精英满级"),
        ("无精英一级", "无精英1级"),
        ("无精英1级队", "无精英1级"),
    ])
    def test_alias_mapping(self, alias, expected):
        assert normalize_category(alias) == expected

    def test_not_found_returns_none(self):
        assert normalize_category("不存在的流派") is None

    def test_empty_string(self):
        assert normalize_category("") is None

    def test_whitespace_only(self):
        assert normalize_category("   ") is None

    def test_strips_whitespace(self):
        """函数会 strip()，前后空格不影响匹配"""
        assert normalize_category("四星队 ") == "四星队"
        assert normalize_category(" 四星队") == "四星队"

    def test_internal_spaces_not_stripped(self):
        """中间空格不匹配"""
        assert normalize_category("四 星队") is None

    def test_categories_count(self):
        assert len(CATEGORIES) == 7

    def test_aliases_not_empty(self):
        assert len(CATEGORY_ALIASES) > 0
