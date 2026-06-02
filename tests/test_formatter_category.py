"""formatter/category.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from formatter.category import format_categories
from resolver.category import CATEGORIES


class TestFormatCategories:
    def test_contains_all_categories(self):
        result = format_categories()
        for cat in CATEGORIES:
            assert cat in result

    def test_header_present(self):
        result = format_categories()
        assert "🏷️" in result

    def test_four_star_team(self):
        result = format_categories()
        assert "四星队" in result

    def test_no_elite_level1(self):
        result = format_categories()
        assert "无精英1级" in result

    def test_is_string(self):
        result = format_categories()
        assert isinstance(result, str)

    def test_not_empty(self):
        result = format_categories()
        assert len(result) > 0
