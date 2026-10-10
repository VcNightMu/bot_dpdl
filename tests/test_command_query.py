# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: query.py 单元测试 - 验证 #查 指令的参数解析和API调用
# 模型: mimo/mimo-v2.5


import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""qq_bot/commands/query.py 单元测试"""

import sys
import re
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass, field

pass  # 仓库根已由 _REPO_ROOT 注入 sys.path

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

    @pytest.mark.asyncio
    async def test_annihilation_cn_name_query(self):
        """剿灭关卡中文名查询：解析出地区名+关卡名一起传"""
        match = make_match("#查 多索雷斯换水口 四星队")
        mock_result = MockQueryResult()
        operation_index = {
            "by_operation": {},
            "by_cn_name": {
                "多索雷斯换水口": {
                    "operation": "玻利瓦尔",
                    "cn_name": "多索雷斯换水口",
                    "episode": "轮换委托",
                    "story": "剿灭作战",
                    "has_challenge": False,
                }
            },
            "duplicates": {},
        }

        with patch("qq_bot.commands.query.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.query.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.query_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_query(match, group_id=1, user_id=1, operation_index=operation_index)

            call_kwargs = mock_instance.query_records.call_args.kwargs
            assert call_kwargs["operation"] == "玻利瓦尔"
            assert call_kwargs["cn_name"] == "多索雷斯换水口"
            assert call_kwargs["category"] == "四星队"

    @pytest.mark.asyncio
    async def test_operation_code_query_with_index(self):
        """代号查询（带索引）：解析出 operation + cn_name 一起传"""
        match = make_match("#查 H11-1 四星队")
        mock_result = MockQueryResult()
        operation_index = {
            "by_operation": {
                "H11-1": {
                    "operation": "H11-1",
                    "cn_name": "尘霾行动-1",
                    "episode": "淬火尘霾",
                    "story": "主线关卡",
                    "has_challenge": True,
                }
            },
            "by_cn_name": {},
            "duplicates": {},
        }

        with patch("qq_bot.commands.query.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.query.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.query_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_query(match, group_id=1, user_id=1, operation_index=operation_index)

            call_kwargs = mock_instance.query_records.call_args.kwargs
            assert call_kwargs["operation"] == "H11-1"
            assert call_kwargs["cn_name"] == "尘霾行动-1"
            assert call_kwargs["category"] == "四星队"
