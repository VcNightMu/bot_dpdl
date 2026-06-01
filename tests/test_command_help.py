# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: help.py 单元测试 - 验证 #help 指令处理
# 模型: mimo/mimo-v2.5

"""qq_bot/commands/help.py 单元测试"""

import sys
import re
import pytest

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from qq_bot.commands.help import handle_help


@pytest.fixture
def match():
    """模拟正则匹配对象"""
    m = re.match(r"^#help$", "#help")
    return m


class TestHandleHelp:
    """测试 handle_help"""

    @pytest.mark.asyncio
    async def test_returns_string(self, match):
        """返回值是字符串"""
        result = await handle_help(match, group_id=1, user_id=1)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_contains_commands(self, match):
        """输出包含指令列表"""
        result = await handle_help(match, group_id=1, user_id=1)
        assert "#查" in result
        assert "#未通关" in result
        assert "#待压人" in result
        assert "#流派" in result
        assert "#help" in result

    @pytest.mark.asyncio
    async def test_contains_examples(self, match):
        """输出包含使用示例"""
        result = await handle_help(match, group_id=1, user_id=1)
        assert "示例" in result or "H11-1" in result

    @pytest.mark.asyncio
    async def test_group_and_user_id_ignored(self, match):
        """group_id 和 user_id 不影响输出"""
        result1 = await handle_help(match, group_id=100, user_id=200)
        result2 = await handle_help(match, group_id=300, user_id=400)
        assert result1 == result2
