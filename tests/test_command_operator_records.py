# -*- coding: utf-8 -*-
# 日期：2026-08-25
# 开发者：橘雪莉
# 功能摘要：operator_records.py 单元测试 - 验证 #干员记录 指令的参数解析和API调用
# 模型：deepseek-v4-pro

"""qq_bot/commands/operator_records.py 单元测试"""

import re
import sys
from dataclasses import dataclass, field

import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from api_client import WikiAPIValidationError
from qq_bot.commands.operator_records import (
    _extract_friendly_message,
    _parse_combo,
    handle_operator_records,
)


@dataclass
class MockSearchResult:
    count: int = 375
    count_valid: int = 375
    records: list = field(default_factory=list)


def make_match(text: str):
    return re.match(r"^#干员记录\s+(.+)", text)


class TestHandleOperatorRecords:
    @pytest.mark.asyncio
    async def test_missing_args_returns_hint(self):
        """无参数时返回提示"""
        # 无参数由 handler 的 _no_args 分支处理，这里测单参数
        match = make_match("#干员记录 羽毛笔")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert isinstance(result, str)
        assert "流派" in result

    @pytest.mark.asyncio
    async def test_non_preset_category_returns_error(self):
        """非预设流派（如黎博利队）返回错误提示"""
        match = make_match("#干员记录 羽毛笔 黎博利队")
        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value=None,
        ):
            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "未找到流派" in result

    @pytest.mark.asyncio
    async def test_operator_is_category_name_returns_hint(self):
        """干员名误填成流派名（参数写反）时提示"""
        match = make_match("#干员记录 精一1级四星队 114")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert isinstance(result, str)
        assert "是流派名" in result
        assert "不是干员" in result

    @pytest.mark.asyncio
    async def test_operator_is_category_alias_returns_hint(self):
        """干员名误填成流派别名（如 114）时提示"""
        match = make_match("#干员记录 114 无精英满级")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert isinstance(result, str)
        assert "是流派名" in result
        assert "不是干员" in result

    @pytest.mark.asyncio
    async def test_alias_normalized(self):
        """固定低星流派别名被归一化（无精英 → 无精英满级）"""
        match = make_match("#干员记录 羽毛笔 无精英")
        mock_result = MockSearchResult()

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_operator_records(match, group_id=1, user_id=1)

            conditions = mock_instance.search_records.call_args.kwargs["conditions"]
            assert conditions[1]["value"] == "无精英满级"

    @pytest.mark.asyncio
    async def test_successful_query_shows_count(self):
        """正常查询回显总记录/有效记录/旧纪录三行"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        mock_result = MockSearchResult(count=375, count_valid=375)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "羽毛笔" in result
            assert "无精英满级" in result
            assert "总记录：375 条" in result
            assert "有效记录：375 条" in result
            assert "旧纪录：0 条" in result

    @pytest.mark.asyncio
    async def test_query_conditions_passed_correctly(self):
        """验证传给 search_records 的 conditions 结构正确"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        mock_result = MockSearchResult()

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_operator_records(match, group_id=1, user_id=1)

            call_kwargs = mock_instance.search_records.call_args.kwargs
            conditions = call_kwargs["conditions"]
            assert len(conditions) == 2
            assert conditions[0] == {
                "field": "team",
                "value": {"members": [{"operator": "羽毛笔"}]},
            }
            assert conditions[1] == {"field": "category", "value": "无精英满级"}

    @pytest.mark.asyncio
    async def test_multiword_operator_name(self):
        """带空格的英文名：最后一个词作为流派"""
        match = make_match("#干员记录 La Pluma 无精英满级")
        mock_result = MockSearchResult()

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_operator_records(match, group_id=1, user_id=1)

            conditions = mock_instance.search_records.call_args.kwargs["conditions"]
            assert conditions[0]["value"]["members"][0]["operator"] == "La Pluma"

    @pytest.mark.asyncio
    async def test_count_with_old_records_shows_note(self):
        """含旧纪录时三行分别展示总数/有效/旧纪录"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        mock_result = MockSearchResult(count=503, count_valid=375)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "总记录：503 条" in result
            assert "有效记录：375 条" in result
            assert "旧纪录：128 条" in result

    @pytest.mark.asyncio
    async def test_zero_records_returns_empty_hint(self):
        """无记录时返回提示"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        mock_result = MockSearchResult(count=0, count_valid=0)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "没有找到记录" in result

    @pytest.mark.asyncio
    async def test_api_error_returns_fallback(self):
        """API 异常时返回错误提示"""
        match = make_match("#干员记录 羽毛笔 无精英满级")

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(side_effect=Exception("超时"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "失败" in result or "重试" in result

    @pytest.mark.asyncio
    async def test_operator_not_found_returns_friendly_message(self):
        """干员不存在时返回服务端友好提示"""
        match = make_match("#干员记录 不存在的干员XYZ 无精英满级")

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            exc = WikiAPIValidationError(
                '{"error":"bad_request","message":"干员「不存在的干员XYZ」未识别"}'
            )
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(side_effect=exc)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert result == "干员「不存在的干员XYZ」未识别"


class TestExtractFriendlyMessage:
    """_extract_friendly_message 函数单元测试"""

    def test_parses_json_message(self):
        """从 400 错误中提取友好提示"""
        exc = WikiAPIValidationError(
            '{"error":"bad_request","message":"干员「羽毛笔」未识别"}'
        )
        assert _extract_friendly_message(exc) == "干员「羽毛笔」未识别"

    def test_non_json_returns_none(self):
        """非 JSON 错误返回 None"""
        exc = WikiAPIValidationError("plain error without json")
        assert _extract_friendly_message(exc) is None

    def test_no_message_field_returns_none(self):
        """JSON 但无 message 字段返回 None"""
        exc = WikiAPIValidationError('{"error":"validation","issues":[]}')
        assert _extract_friendly_message(exc) is None


class TestParseCombo:
    """_parse_combo 函数单元测试"""

    def test_split_by_plus(self):
        assert _parse_combo("羽毛笔+银灰") == ["羽毛笔", "银灰"]

    def test_three_operators(self):
        assert _parse_combo("羽毛笔+银灰+史尔特尔") == ["羽毛笔", "银灰", "史尔特尔"]

    def test_strips_whitespace(self):
        assert _parse_combo(" 羽毛笔 + 银灰 ") == ["羽毛笔", "银灰"]

    def test_skips_empty_items(self):
        assert _parse_combo("羽毛笔+") == ["羽毛笔"]
        assert _parse_combo("+羽毛笔") == ["羽毛笔"]
        assert _parse_combo("+") == []

    def test_dedup_preserves_order(self):
        assert _parse_combo("羽毛笔+银灰+羽毛笔") == ["羽毛笔", "银灰"]

    def test_multiword_name_kept_intact(self):
        assert _parse_combo("La Pluma+Texas the Omertosa") == ["La Pluma", "Texas the Omertosa"]


class TestComboQuery:
    """#干员记录 组合查询测试（组合查询限定在某个流派上）"""

    def _mock_client(self, result=None, exc=None):
        """构造 mock WikiClient 实例。"""
        mock_instance = AsyncMock()
        if exc is not None:
            mock_instance.search_records = AsyncMock(side_effect=exc)
        else:
            mock_instance.search_records = AsyncMock(return_value=result)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        return mock_instance

    @pytest.mark.asyncio
    async def test_combo_conditions_passed_correctly(self):
        """组合查询 conditions 为 team(多干员AND) + category 两条"""
        match = make_match("#干员记录 羽毛笔+银灰 无精英满级")
        mock_result = MockSearchResult(count=120, count_valid=120)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            await handle_operator_records(match, group_id=1, user_id=1)

            conditions = mock_instance.search_records.call_args.kwargs["conditions"]
            assert len(conditions) == 2
            assert conditions[0] == {
                "field": "team",
                "value": {
                    "members": [
                        {"operator": "羽毛笔"},
                        {"operator": "银灰"},
                    ],
                },
            }
            assert conditions[1] == {"field": "category", "value": "无精英满级"}

    @pytest.mark.asyncio
    async def test_combo_shows_stats(self):
        """组合查询回显三行统计（含流派）"""
        match = make_match("#干员记录 羽毛笔+银灰 无精英满级")
        mock_result = MockSearchResult(count=120, count_valid=120)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "羽毛笔+银灰" in result
            assert "无精英满级" in result
            assert "总记录：120 条" in result
            assert "有效记录：120 条" in result
            assert "旧纪录：0 条" in result

    @pytest.mark.asyncio
    async def test_combo_old_records(self):
        """组合查询含旧纪录时旧纪录单独标注"""
        match = make_match("#干员记录 羽毛笔+银灰 无精英满级")
        mock_result = MockSearchResult(count=200, count_valid=120)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "旧纪录：80 条" in result

    @pytest.mark.asyncio
    async def test_combo_zero_records(self):
        """组合查询无记录时返回提示"""
        match = make_match("#干员记录 羽毛笔+银灰 无精英满级")
        mock_result = MockSearchResult(count=0, count_valid=0)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "没有找到同时上场的记录" in result

    @pytest.mark.asyncio
    async def test_combo_missing_category_returns_hint(self):
        """组合查询缺流派时提示"""
        match = make_match("#干员记录 羽毛笔+银灰")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert "流派" in result

    @pytest.mark.asyncio
    async def test_combo_single_after_dedup_returns_hint(self):
        """去重后只剩一个干员时提示至少两个"""
        match = make_match("#干员记录 羽毛笔+羽毛笔 无精英满级")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert "至少需要两个干员" in result

    @pytest.mark.asyncio
    async def test_combo_empty_returns_hint(self):
        """仅 + 号时提示至少两个"""
        match = make_match("#干员记录 + 无精英满级")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert "至少需要两个干员" in result

    @pytest.mark.asyncio
    async def test_combo_too_many_operators(self):
        """超过 13 个干员时提示上限"""
        ops = "+".join(f"干员{i}" for i in range(14))
        match = make_match(f"#干员记录 {ops} 无精英满级")
        result = await handle_operator_records(match, group_id=1, user_id=1)
        assert "最多支持 13 个干员" in result

    @pytest.mark.asyncio
    async def test_combo_operator_not_found(self):
        """组合中干员未识别时返回服务端友好提示"""
        match = make_match("#干员记录 羽毛笔+不存在的干员XYZ 无精英满级")

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            exc = WikiAPIValidationError(
                '{"error":"bad_request","message":"干员「不存在的干员XYZ」未识别"}'
            )
            mock_instance = self._mock_client(exc=exc)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert result == "干员「不存在的干员XYZ」未识别"
