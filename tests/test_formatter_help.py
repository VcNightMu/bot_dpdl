"""formatter/help.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from formatter.help import format_help


class TestFormatHelp:
    def test_contains_all_commands(self):
        result = format_help()
        assert "#查" in result
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
