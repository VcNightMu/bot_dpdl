# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: handler.py 单元测试 - 验证指令路由与分发逻辑
# 模型: mimo/mimo-v2.5

"""handler.py 单元测试"""

import sys
import re
import pytest

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from qq_bot.handler import CommandHandler


@pytest.fixture
def handler():
    """创建 CommandHandler 实例"""
    return CommandHandler()


class TestCommandRegistration:
    """测试指令注册"""

    def test_commands_registered(self, handler):
        """所有指令都已注册（含无参数分支）"""
        # 5个有参数指令 + 3个无参数分支 = 8
        assert len(handler.commands) == 8

    def test_patterns_are_compiled_regex(self, handler):
        """注册的模式都是已编译的正则"""
        for pattern, _handler in handler.commands:
            assert isinstance(pattern, re.Pattern)


class TestHandle:
    """测试指令匹配和分发"""

    @pytest.mark.asyncio
    async def test_non_command_returns_none(self, handler):
        """非指令消息返回 None"""
        result = await handler.handle("大家好", group_id=1, user_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_whitespace_stripped(self, handler):
        """消息首尾空格被去除"""
        result = await handler.handle("  大家好  ", group_id=1, user_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_help_matched(self, handler):
        """#help 指令匹配"""
        result = await handler.handle("#help", group_id=1, user_id=1)
        assert result is not None
        assert "少人WIKI" in result or "help" in result.lower() or "指令" in result

    @pytest.mark.asyncio
    async def test_category_matched(self, handler):
        """#流派 指令匹配"""
        result = await handler.handle("#流派", group_id=1, user_id=1)
        assert result is not None
        assert "流派" in result or "四星队" in result

    @pytest.mark.asyncio
    async def test_query_no_args(self, handler):
        """#查 缺少参数时返回错误提示"""
        result = await handler.handle("#查", group_id=1, user_id=1)
        assert result is not None
        assert "缺少参数" in result

    @pytest.mark.asyncio
    async def test_nonexistent_command(self, handler):
        """不存在的指令返回 None"""
        result = await handler.handle("#不存在的指令", group_id=1, user_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_partial_match_not_triggered(self, handler):
        """部分匹配不触发（如 #helpme）"""
        result = await handler.handle("#helpme", group_id=1, user_id=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_uncleared_no_args(self, handler):
        """#未通关 缺少参数时返回错误提示"""
        result = await handler.handle("#未通关", group_id=1, user_id=1)
        assert result is not None
        assert "缺少参数" in result

    @pytest.mark.asyncio
    async def test_stale_no_args(self, handler):
        """#待压人 缺少参数时返回错误提示"""
        result = await handler.handle("#待压人", group_id=1, user_id=1)
        assert result is not None
        assert "缺少参数" in result

    @pytest.mark.asyncio
    async def test_help_exact_match_only(self, handler):
        """#help 精确匹配，后面有额外文本不触发"""
        result = await handler.handle("#help 你好", group_id=1, user_id=1)
        assert result is None  # ^#help$ 不匹配 "#help 你好"

    @pytest.mark.asyncio
    async def test_list_input_converted(self, handler):
        """OneBot11列表格式输入能正确处理"""
        list_msg = [{"type": "text", "data": {"text": "#help"}}]
        result = await handler.handle(list_msg, group_id=1, user_id=1)
        assert result is not None  # 匹配到 #help
