# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: uncleared.py 单元测试 - 验证 #未通关 指令的参数解析和API调用
# 模型: mimo/mimo-v2.5

"""qq_bot/commands/uncleared.py 单元测试"""

import sys
import re
import pytest
from unittest.mock import AsyncMock, patch
from dataclasses import dataclass, field

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from qq_bot.commands.uncleared import handle_uncleared, _resolve_uncleared


# --- Mock 数据 ---

MockUnclearedRecord = {
    "operation": "TR-22",
    "cn_name": "明辨是非",
    "has_challenge": False,
}


@dataclass
class MockUnclearedResult:
    episode: str = "惊霆无声"
    category: str = "四星队"
    uncleared: list = field(default_factory=lambda: [dict(MockUnclearedRecord)])


def make_match(text: str):
    """创建正则匹配对象"""
    return re.match(r"^#未通关\s+(.+)", text)


class TestHandleUncleared:
    """测试 handle_uncleared"""

    @pytest.mark.asyncio
    async def test_missing_category_returns_hint(self):
        """缺少流派参数时返回提示"""
        match = make_match("#未通关 惊霆无声")
        result = await handle_uncleared(match, group_id=1, user_id=1)
        assert "缺少流派" in result or "流派" in result

    @pytest.mark.asyncio
    async def test_invalid_category_returns_error(self):
        """无效流派名返回错误提示"""
        match = make_match("#未通关 惊霆无声 不存在的流派")
        with patch("qq_bot.commands.uncleared.normalize_category", return_value=None):
            result = await handle_uncleared(match, group_id=1, user_id=1)
            assert "未找到流派" in result

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """正常查询返回格式化结果"""
        match = make_match("#未通关 惊霆无声 四星队")
        mock_result = MockUnclearedResult()

        with patch("qq_bot.commands.uncleared.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(return_value=mock_result)
            mock_instance.query_records = AsyncMock(return_value=AsyncMock(records=[]))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_uncleared(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "惊霆无声" in result or "TR-22" in result

    @pytest.mark.asyncio
    async def test_api_error_returns_fallback(self):
        """API 异常时返回错误提示"""
        match = make_match("#未通关 惊霆无声 四星队")

        with patch("qq_bot.commands.uncleared.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(side_effect=Exception("API 超时"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_uncleared(match, group_id=1, user_id=1)
            assert "失败" in result or "重试" in result

    @pytest.mark.asyncio
    async def test_empty_uncleared(self):
        """没有未通关关卡时返回空结果"""
        match = make_match("#未通关 惊霆无声 四星队")
        mock_result = MockUnclearedResult(uncleared=[])

        with patch("qq_bot.commands.uncleared.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_uncleared(match, group_id=1, user_id=1)
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_operation_index_passed(self):
        """operation_index 正确传递给 format_uncleared"""
        match = make_match("#未通关 惊霆无声 四星队")
        mock_result = MockUnclearedResult()
        test_index = {"by_operation": {"TR-22": {"cn_name": "明辨是非"}}}

        with patch("qq_bot.commands.uncleared.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient, \
             patch("qq_bot.commands.uncleared.format_uncleared") as mock_fmt:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(return_value=mock_result)
            mock_instance.query_records = AsyncMock(return_value=AsyncMock(records=[]))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance
            mock_fmt.return_value = "formatted result"

            result = await handle_uncleared(match, group_id=1, user_id=2, operation_index=test_index)
            # 验证 format_uncleared 被调用且传入了 operation_index
            call_args = mock_fmt.call_args
            assert call_args[0][3] is test_index  # 第4个参数是 operation_index

    @pytest.mark.asyncio
    async def test_filter_removes_challenge_covered(self):
        """突袭有记录时，从uncleared中剔除该关卡"""

        @dataclass
        class MockRecord:
            operation_type: str = "normal"

        @dataclass
        class MockQueryResult:
            records: list = None
            def __post_init__(self):
                if self.records is None:
                    self.records = []

        uncleared = [
            {"operation": "17-10", "cn_name": "裂变临界", "difficulty": "challenge", "hasChallenge": True},
            {"operation": "17-11", "cn_name": "归程信号", "difficulty": "challenge", "hasChallenge": True},
            {"operation": "TR-28", "cn_name": "人权宣言", "difficulty": "normal", "hasChallenge": False},
        ]

        mock_client = AsyncMock()
        async def fake_query_records(operation, category):
            if operation == "17-10":
                return MockQueryResult(records=[MockRecord(operation_type="challenge")])
            return MockQueryResult(records=[])
        mock_client.query_records = fake_query_records

        result = await _resolve_uncleared(mock_client, uncleared, "精一1级")
        ops = [item["operation"] for item in result]
        assert "17-10" not in ops  # 突袭有记录，被剔除
        assert "17-11" in ops    # 突袭无记录，保留
        assert "TR-28" in ops    # 无突袭，保留

    @pytest.mark.asyncio
    async def test_resolve_both_uncleared_shows_two(self):
        """两种难度都没记录时，显示两条"""

        @dataclass
        class MockQueryResult:
            records: list = None
            def __post_init__(self):
                if self.records is None:
                    self.records = []

        uncleared = [
            {"operation": "17-2", "cn_name": "", "difficulty": "challenge", "hasChallenge": True},
        ]

        mock_client = AsyncMock()
        async def fake_query(operation, category):
            return MockQueryResult(records=[])
        mock_client.query_records = fake_query

        result = await _resolve_uncleared(mock_client, uncleared, "四星队")
        assert len(result) == 2
        diffs = {item["difficulty"] for item in result}
        assert diffs == {"challenge", "normal"}

    @pytest.mark.asyncio
    async def test_resolve_only_normal_records_shows_challenge(self):
        """只有normal有记录时，显示challenge未过"""

        @dataclass
        class MockRecord:
            operation_type: str = "normal"

        @dataclass
        class MockQueryResult:
            records: list = None
            def __post_init__(self):
                if self.records is None:
                    self.records = []

        uncleared = [
            {"operation": "10-8", "cn_name": "", "difficulty": "challenge", "hasChallenge": True},
        ]

        mock_client = AsyncMock()
        async def fake_query(operation, category):
            return MockQueryResult(records=[MockRecord(operation_type="normal")])
        mock_client.query_records = fake_query

        result = await _resolve_uncleared(mock_client, uncleared, "四星队")
        assert len(result) == 1
        assert result[0]["difficulty"] == "challenge"
