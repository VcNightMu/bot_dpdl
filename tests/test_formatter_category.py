
import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""formatter/category.py 单元测试"""
import sys
pass  # 仓库根已由 _REPO_ROOT 注入 sys.path

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
