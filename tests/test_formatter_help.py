
import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""formatter/help.py 单元测试"""
import sys
pass  # 仓库根已由 _REPO_ROOT 注入 sys.path

import pytest
from formatter.help import format_help


class TestFormatHelp:
    def test_contains_all_commands(self):
        result = format_help()
        assert "#查" in result
        assert "#人数" in result
        assert "#未通关" in result
        assert "#待压人" in result
        assert "#流派" in result
        assert "#help" in result

    def test_contains_example(self):
        result = format_help()
        assert "H11-1" in result
        assert "四星队" in result

    def test_contains_header(self):
        result = format_help()
        assert "少人WIKI" in result

    def test_is_string(self):
        result = format_help()
        assert isinstance(result, str)

    def test_not_empty(self):
        result = format_help()
        assert len(result) > 0
