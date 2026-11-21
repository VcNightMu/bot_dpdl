# -*- coding: utf-8 -*-
# 日期：2026-08-25
# 开发者：橘雪莉
# 功能摘要：operator_records.py 单元测试 - 验证 #干员记录 指令的参数解析和API调用
# 模型：deepseek-v4-pro


import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""qq_bot/commands/operator_records.py 单元测试"""

import re
import sys
from dataclasses import dataclass, field

import pytest
from unittest.mock import AsyncMock, patch

pass  # 仓库根已由 _REPO_ROOT 注入 sys.path

from api_client import WikiAPIValidationError
from qq_bot.commands.operator_records import (
    _extract_friendly_message,
    _extract_unrecognized_name,
    _parse_combo,
    _split_operator_skill,
    handle_operator_records,
)


@dataclass
class MockSearchResult:
    count: int = 375
    count_valid: int = 375
    records: list = field(default_factory=list)


def make_search_side_effect(main_count=375, main_valid=375, contract=None):
    """构造 search_records 的 side_effect：主查询返回主结果，合约查询按 story 返回。

    contract: {"危机合约": (count, valid), "危机合约Re": (count, valid)}
    """
    async def _side_effect(conditions=None, **kwargs):
        story = None
        for c in (conditions or []):
            if c.get("field") == "story":
                story = c.get("value")
                break
        if story is None:
            return MockSearchResult(count=main_count, count_valid=main_valid)
        cnt, valid = (contract or {}).get(story, (0, 0))
        return MockSearchResult(count=cnt, count_valid=valid)
    return _side_effect


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

            conditions = mock_instance.search_records.call_args_list[0].kwargs["conditions"]
            assert conditions[1]["value"] == "无精英满级"

    @pytest.mark.asyncio
    async def test_successful_query_shows_count(self):
        """正常查询回显四行统计（总/有效/旧/合约）"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        contract = {"危机合约": (28, 27), "危机合约Re": (1, 1)}

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(
                side_effect=make_search_side_effect(
                    main_count=375, main_valid=375, contract=contract
                )
            )
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert "羽毛笔" in result
            assert "无精英满级" in result
            assert "总记录：375 条" in result
            assert "有效记录：347 条" in result
            assert "合约记录：28 条" in result
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

            call_kwargs = mock_instance.search_records.call_args_list[0].kwargs
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

            conditions = mock_instance.search_records.call_args_list[0].kwargs["conditions"]
            assert conditions[0]["value"]["members"][0]["operator"] == "La Pluma"

    @pytest.mark.asyncio
    async def test_count_with_old_records_shows_note(self):
        """含旧纪录时四行分别展示总数/有效/旧纪录/合约"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        contract = {"危机合约": (28, 27), "危机合约Re": (1, 1)}

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(
                side_effect=make_search_side_effect(
                    main_count=503, main_valid=375, contract=contract
                )
            )
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "总记录：503 条" in result
            assert "有效记录：347 条" in result
            assert "合约记录：28 条" in result
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

    @pytest.mark.asyncio
    async def test_contract_records_counted_separately(self):
        """合约记录单独统计：主查询 + 危机合约 + 危机合约Re 共三次调用"""
        match = make_match("#干员记录 羽毛笔 无精英满级")
        contract = {"危机合约": (28, 27), "危机合约Re": (1, 1)}

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(
                side_effect=make_search_side_effect(
                    main_count=375, main_valid=375, contract=contract
                )
            )
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_operator_records(match, group_id=1, user_id=1)

            assert mock_instance.search_records.call_count == 3
            stories = [
                next(
                    (
                        c["value"]
                        for c in call.kwargs["conditions"]
                        if c["field"] == "story"
                    ),
                    None,
                )
                for call in mock_instance.search_records.call_args_list
            ]
            assert stories == [None, "危机合约", "危机合约Re"]

    @pytest.mark.asyncio
    async def test_contract_query_failure_not_silently_zero(self):
        """合约查询失败时不能静默当 0（否则失败部分被算进「有效记录」）"""
        match = make_match("#干员记录 羽毛笔 无精英满级")

        async def _side_effect(conditions=None, **kwargs):
            for c in (conditions or []):
                if c.get("field") == "story":
                    # 两个合约查询都失败
                    raise RuntimeError("429 rate limited")
            return MockSearchResult(count=100, count_valid=90)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(side_effect=_side_effect)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)

            # 必须显式告知统计不可用，且不能给出会误导的「有效/合约」拆分
            assert "不可用" in result
            assert "有效记录：90" not in result
            assert "合约记录：0" not in result
            assert "总记录：100" in result


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

            conditions = mock_instance.search_records.call_args_list[0].kwargs["conditions"]
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
        """组合查询回显四行统计（含流派、合约）"""
        match = make_match("#干员记录 羽毛笔+银灰 无精英满级")
        contract = {"危机合约": (23, 18), "危机合约Re": (2, 1)}

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(
                result=MockSearchResult(count=120, count_valid=120)
            )
            mock_instance.search_records = AsyncMock(
                side_effect=make_search_side_effect(
                    main_count=120, main_valid=120, contract=contract
                )
            )
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "羽毛笔+银灰" in result
            assert "无精英满级" in result
            assert "总记录：120 条" in result
            assert "有效记录：101 条" in result
            assert "合约记录：19 条" in result
            assert "旧纪录：0 条" in result

    @pytest.mark.asyncio
    async def test_combo_old_records(self):
        """组合查询含旧纪录时旧纪录单独标注，且合约记录单独统计"""
        match = make_match("#干员记录 羽毛笔+银灰 无精英满级")
        contract = {"危机合约": (23, 18), "危机合约Re": (2, 1)}

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(
                result=MockSearchResult(count=200, count_valid=120)
            )
            mock_instance.search_records = AsyncMock(
                side_effect=make_search_side_effect(
                    main_count=200, main_valid=120, contract=contract
                )
            )
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert "合约记录：19 条" in result
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


class TestSkillSuffix:
    """技能号解析：银灰3 → ("银灰", "3")；不写则任意技能"""

    def test_split_with_skill(self):
        assert _split_operator_skill("银灰3") == ("银灰", "3")
        assert _split_operator_skill("银灰1") == ("银灰", "1")
        assert _split_operator_skill("银灰2") == ("银灰", "2")

    def test_split_without_skill(self):
        assert _split_operator_skill("银灰") == ("银灰", None)
        assert _split_operator_skill("La Pluma") == ("La Pluma", None)

    def test_name_ending_with_digit_is_split_first(self):
        """Castle-3 这类名字会先按技能号拆，由调用方在 API 报错后回退。"""
        assert _split_operator_skill("Castle-3") == ("Castle-", "3")
        assert _split_operator_skill("Lancet-2") == ("Lancet-", "2")

    def test_no_split_cases(self):
        # 结尾不是 1/2/3，或纯数字（名字至少 1 字符）
        assert _split_operator_skill("12F") == ("12F", None)
        assert _split_operator_skill("3") == ("3", None)
        assert _split_operator_skill("4") == ("4", None)
        assert _split_operator_skill("") == ("", None)

    def test_extract_unrecognized_name(self):
        msg = "干员「Castle-」未识别"
        assert _extract_unrecognized_name(msg) == "Castle-"
        assert _extract_unrecognized_name("参数错误") is None
        assert _extract_unrecognized_name("") is None


class TestSkillQuery:
    """#干员记录 指定技能查询"""

    def _mock_client(self, result=None, exc=None, side_effect=None):
        mock_instance = AsyncMock()
        if side_effect is not None:
            mock_instance.search_records = AsyncMock(side_effect=side_effect)
        elif exc is not None:
            mock_instance.search_records = AsyncMock(side_effect=exc)
        else:
            mock_instance.search_records = AsyncMock(return_value=result)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        return mock_instance

    @pytest.mark.asyncio
    async def test_single_operator_with_skill(self):
        """银灰3 → members 带 skill=3"""
        match = make_match("#干员记录 银灰3 无精英满级")
        mock_result = MockSearchResult(count=42, count_valid=42)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)

            members = mock_instance.search_records.call_args_list[0].kwargs[
                "conditions"][0]["value"]["members"]
            assert members == [{"operator": "银灰", "skill": "3"}]
            assert "银灰（3技能）" in result

    @pytest.mark.asyncio
    async def test_single_operator_without_skill_unchanged(self):
        """不写技能号时 members 不带 skill 字段（任意技能）"""
        match = make_match("#干员记录 银灰 无精英满级")
        mock_result = MockSearchResult(count=550, count_valid=550)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)

            members = mock_instance.search_records.call_args_list[0].kwargs[
                "conditions"][0]["value"]["members"]
            assert members == [{"operator": "银灰"}]
            assert "技能" not in result

    @pytest.mark.asyncio
    async def test_combo_with_mixed_skills(self):
        """组合里可分别指定技能，未指定的仍是任意技能"""
        match = make_match("#干员记录 羽毛笔1+银灰3+史尔特尔 无精英满级")
        mock_result = MockSearchResult(count=7, count_valid=7)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(result=mock_result)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)

            members = mock_instance.search_records.call_args_list[0].kwargs[
                "conditions"][0]["value"]["members"]
            assert members == [
                {"operator": "羽毛笔", "skill": "1"},
                {"operator": "银灰", "skill": "3"},
                {"operator": "史尔特尔"},
            ]
            assert "羽毛笔（1技能）" in result
            assert "银灰（3技能）" in result
            assert "史尔特尔（" not in result

    @pytest.mark.asyncio
    async def test_fallback_for_name_ending_with_digit(self):
        """Castle-3：先按技能号拆，API 报未识别后回退为完整干员名"""
        match = make_match("#干员记录 Castle-3 无精英满级")
        exc = WikiAPIValidationError(
            '{"error":"bad_request","message":"干员「Castle-」未识别"}'
        )
        mock_result = MockSearchResult(count=5, count_valid=5)

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(
                side_effect=[exc, mock_result,
                             MockSearchResult(0, 0), MockSearchResult(0, 0)]
            )
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)

            calls = mock_instance.search_records.call_args_list
            first = calls[0].kwargs["conditions"][0]["value"]["members"]
            second = calls[1].kwargs["conditions"][0]["value"]["members"]
            assert first == [{"operator": "Castle-", "skill": "3"}]
            assert second == [{"operator": "Castle-3"}]
            assert "总记录：5 条" in result

    @pytest.mark.asyncio
    async def test_unknown_operator_still_reports_friendly_message(self):
        """真正不存在的干员：回退一次后仍失败，返回服务端提示（不无限重试）"""
        match = make_match("#干员记录 不存在的干员3 无精英满级")
        exc = WikiAPIValidationError(
            '{"error":"bad_request","message":"干员「不存在的干员」未识别"}'
        )

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(exc=exc)
            MockClient.return_value = mock_instance

            result = await handle_operator_records(match, group_id=1, user_id=1)
            assert result == "干员「不存在的干员」未识别"
            # 首次 + 回退重试，最多两次
            assert mock_instance.search_records.call_count == 2

    @pytest.mark.asyncio
    async def test_no_skill_no_retry(self):
        """未指定技能时即使报未识别也不重试（没有可回退的拆分）"""
        match = make_match("#干员记录 不存在的干员 无精英满级")
        exc = WikiAPIValidationError(
            '{"error":"bad_request","message":"干员「不存在的干员」未识别"}'
        )

        with patch(
            "qq_bot.commands.operator_records.normalize_category",
            return_value="无精英满级",
        ), patch("qq_bot.commands.operator_records.WikiClient") as MockClient:
            mock_instance = self._mock_client(exc=exc)
            MockClient.return_value = mock_instance

            await handle_operator_records(match, group_id=1, user_id=1)
            assert mock_instance.search_records.call_count == 1
