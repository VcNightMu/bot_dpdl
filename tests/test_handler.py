# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: handler.py 单元测试 - 验证指令路由与分发逻辑
# 模型: mimo/mimo-v2.5


import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""handler.py 单元测试"""

import sys
import re
import pytest

pass  # 仓库根已由 _REPO_ROOT 注入 sys.path

from qq_bot.handler import CommandHandler


_CMD_NAME_RE = re.compile(r"\^?(#[^\s\\$()*+?\[\]{}|]+)")


def _routed_commands(handler) -> set[str]:
    """路由表里注册的指令名集合。

    路由两种形态：
        有参数  '^#干员记录\\s+(.+)'
        无参数  '^#help$'
    统一用正则抓出命令名（跳过转义与重复限定符，避免把 '(+)' 里的 '+' 当命令）。
    """
    names = set()
    for pattern, _ in handler.commands:
        m = _CMD_NAME_RE.match(pattern.pattern)
        if m:
            names.add(m.group(1))
    return names


def _help_commands() -> set[str]:
    """#help 文本里作为「指令说明行」列出的命令集合（行首以 # 开头）。"""
    from formatter.help import format_help

    return {
        line.split()[0]
        for line in format_help().splitlines()
        if line.startswith("#")
    }


@pytest.fixture
def handler():
    """创建 CommandHandler 实例"""
    return CommandHandler()


class TestCommandRegistration:
    """测试指令注册"""

    def test_commands_registered(self, handler):
        """所有指令都已注册（含无参数分支）"""
        # 8个有参数指令 + 6个无参数分支 = 14
        assert len(handler.commands) == 14

    def test_every_routed_command_is_documented_in_help(self, handler):
        """防漂移：每条已注册指令都必须在 #help 里说明。

        历史教训：加了新指令却忘了更新 formatter/help.py，
        用户查帮助看不到新功能。这条测试锁死两者的对应关系——
        以后新增指令如果没写进 help，这里会直接失败。
        """
        missing = _routed_commands(handler) - _help_commands()

        assert not missing, (
            f"这些指令已注册但没写进 #help：{sorted(missing)}。"
            f"请更新 formatter/help.py 的指令列表。"
        )

    def test_help_has_no_phantom_commands(self, handler):
        """反向：help 里不该出现根本没注册的指令（避免文档吹牛）"""
        phantom = _help_commands() - _routed_commands(handler)

        assert not phantom, f"#help 里列出了未注册的指令：{sorted(phantom)}"

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
    async def test_operation_info_no_args(self, handler):
        """#人数 缺少参数时返回错误提示"""
        result = await handler.handle("#人数", group_id=1, user_id=1)
        assert result is not None
        assert "缺少参数" in result

    @pytest.mark.asyncio
    async def test_operator_records_no_args(self, handler):
        """#干员记录 缺少参数时返回错误提示"""
        result = await handler.handle("#干员记录", group_id=1, user_id=1)
        assert result is not None
        assert "缺少参数" in result

    @pytest.mark.asyncio
    async def test_list_input_converted(self, handler):
        """OneBot11列表格式输入能正确处理"""
        list_msg = [{"type": "text", "data": {"text": "#help"}}]
        result = await handler.handle(list_msg, group_id=1, user_id=1)
        assert result is not None  # 匹配到 #help

    @pytest.mark.asyncio
    async def test_list_input_with_trailing_whitespace(self, handler):
        """数组格式带尾随空格/换行仍能匹配（回归：曾导致 Bot 静默不响应）"""
        for text in ("#help ", "#help\n", " #help", "#流派\n"):
            list_msg = [{"type": "text", "data": {"text": text}}]
            result = await handler.handle(list_msg, group_id=1, user_id=1)
            assert result is not None, f"{text!r} 未能匹配到指令"

    @pytest.mark.asyncio
    async def test_list_input_multi_segment(self, handler):
        """多段文本拼接后再匹配"""
        list_msg = [
            {"type": "text", "data": {"text": "#help"}},
            {"type": "text", "data": {"text": " "}},
        ]
        result = await handler.handle(list_msg, group_id=1, user_id=1)
        assert result is not None
