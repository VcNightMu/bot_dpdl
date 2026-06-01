# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: query.py 单元测试 - 验证 #查 指令的参数解析和API调用
# 模型: mimo/mimo-v2.5

"""qq_bot/commands/query.py 单元测试"""

import sys
import re
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass, field

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from qq_bot.commands.query import handle_query


# --- Mock 数据 ---

@dataclass
class MockBotRecord:
    operation: str = "H11-1"
    cn_name: str = "尘霾行动-1"
    operation_type: str = "normal"
    category: list = field(default_factory=lambda: ["四星队"])
    raider: str = "测试玩家"
    team: list = field(default_factory=lambda: [{"name": "布丁", "skillStr": "2"}])
    date_published: str = "2023-05-12T12:59:28.000Z"
    url: str = "https://www.bilibili.com/video/BV1xxx"
    story: str = "主线关卡"
    episode: str = "淬火尘霾"
    group: str = ""
    is_recommended: bool = False
    remark1: str = ""


@dataclass
class MockQueryResult:
    count: int = 1
    count_valid: int = 1
    records: list = field(default_factory=lambda: [MockBotRecord()])


def make_match(text: str):
    """创建正则匹配对象"""
    return re.match(r"^#查\s+(.+)", text)


class TestHandleQuery:
    """测试 handle_query"""

    @pytest.mark.asyncio
    async def test_missing_category_returns_hint(self):
        """缺少流派参数时返回提示"""
        match = make_match("#查 H11-1")
        result = await handle_query(match, group_id=1, user_id=1)
        assert isinstance(result, str)
        assert "缺少流派" in result or "流派" in result

    @pytest.mark.asyncio
    async def test_invalid_category_returns_error(self):
        """无效流派名返回错误提示"""
        match = make_match("#查 H11-1 不存在的流派XYZ")
        with patch("qq_bot.commands.query.normalize_category", return_value=None):
            result = await handle_query(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "未找到流派" in result

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """正常查询返回格式化结果"""
        match = make_match("#查 H11-1 四星队")
        mock_result = MockQueryResult()

        with patch("qq_bot.commands.query.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.query.normalize_operation", return_value="H11-1"), \
             patch("qq_bot.commands.query.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.query_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_query(match, group_id=1, user_id=1)
            assert result is not None

    @pytest.mark.asyncio
    async def test_api_error_returns_fallback(self):
        """API 异常时返回错误提示"""
        match = make_match("#查 H11-1 四星队")

        with patch("qq_bot.commands.query.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.query.normalize_operation", return_value="H11-1"), \
             patch("qq_bot.commands.query.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.query_records = AsyncMock(side_effect=Exception("API 超时"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_query(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "失败" in result or "重试" in result

    @pytest.mark.asyncio
    async def test_empty_records_returns_no_result(self):
        """查询结果为空时返回提示"""
        match = make_match("#查 H11-1 四星队")
        mock_result = MockQueryResult(count=0, count_valid=0, records=[])

        with patch("qq_bot.commands.query.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.query.normalize_operation", return_value="H11-1"), \
             patch("qq_bot.commands.query.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.query_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_query(match, group_id=1, user_id=1)
            assert isinstance(result, list)
            assert "没有找到" in result[0]

    @pytest.mark.asyncio
    async def test_only_one_arg_returns_hint(self):
        """只有一个参数（没有空格分隔）返回提示"""
        match = make_match("#查 H11-1")
        result = await handle_query(match, group_id=1, user_id=1)
        assert "缺少流派" in result or "流派" in result
