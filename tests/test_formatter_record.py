"""formatter/record.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from formatter.record import (
    format_single_record,
    format_records,
    _format_operator_list,
    _operation_type_label,
    _format_date,
    MAX_MSG_LENGTH,
)


# --- 内部函数测试 ---

class TestFormatOperatorList:
    def test_normal_team(self):
        team = [
            {"name": "司霆惊蛰", "skillStr": "1"},
            {"name": "黑角", "skillStr": "1"},
        ]
        assert _format_operator_list(team) == "司霆惊蛰(1), 黑角(1)"

    def test_empty_team(self):
        assert _format_operator_list([]) == "无干员"

    def test_single_operator(self):
        team = [{"name": "红豆", "skillStr": "7"}]
        assert _format_operator_list(team) == "红豆(7)"

    def test_missing_skill(self):
        team = [{"name": "测试"}]
        assert _format_operator_list(team) == "测试(?)"

    def test_missing_name(self):
        team = [{"skillStr": "1"}]
        assert _format_operator_list(team) == "???(1)"


class TestOperationTypeLabel:
    def test_challenge(self):
        assert _operation_type_label("challenge") == "突袭"

    def test_normal(self):
        assert _operation_type_label("normal") == "普通"

    def test_unknown_defaults_normal(self):
        assert _operation_type_label("unknown") == "普通"

    def test_empty_string(self):
        assert _operation_type_label("") == "普通"


class TestFormatDate:
    def test_iso_format(self):
        result = _format_date("2023-05-12T12:59:28.000Z")
        assert result == "2023-05-12"

    def test_date_only(self):
        result = _format_date("2023-05-12")
        assert result == "2023-05-12"

    def test_empty_string(self):
        assert _format_date("") == "???"

    def test_unknown_format_passthrough(self):
        assert _format_date("昨天") == "昨天"

    def test_datetime_no_z(self):
        result = _format_date("2023-05-12T12:59:28")
        assert result == "2023-05-12"


# --- format_single_record 测试 ---

SAMPLE_RECORD = {
    "operation": "H11-1",
    "cn_name": "惊霆行动-1",
    "operation_type": "challenge",
    "category": ["四星队"],
    "raider": "玩家A",
    "team": [
        {"name": "司霆惊蛰", "skillStr": "1"},
        {"name": "黑角", "skillStr": "1"},
    ],
    "date_published": "2025-12-01",
    "url": "https://www.bilibili.com/video/BV1test123",
}


class TestFormatSingleRecord:
    def test_basic_format(self):
        result = format_single_record(SAMPLE_RECORD)
        assert "H11-1" in result
        assert "惊霆行动-1" in result
        assert "突袭" in result
        assert "玩家A" in result
        assert "BV1test123" in result
        assert "司霆惊蛰(1)" in result

    def test_without_index(self):
        result = format_single_record(SAMPLE_RECORD)
        assert "1️⃣" not in result

    def test_with_index(self):
        result = format_single_record(SAMPLE_RECORD, index=2)
        assert "2️⃣" in result

    def test_category_as_string(self):
        """category 可以是字符串"""
        rec = {**SAMPLE_RECORD, "category": "四星队"}
        result = format_single_record(rec)
        assert "四星队" in result

    def test_category_empty_list(self):
        rec = {**SAMPLE_RECORD, "category": []}
        result = format_single_record(rec)
        assert "???" in result

    def test_missing_fields(self):
        result = format_single_record({})
        assert "???" in result
        assert "无干员" in result
        assert "非B站视频" in result

    def test_normal_type(self):
        rec = {**SAMPLE_RECORD, "operation_type": "normal"}
        result = format_single_record(rec)
        assert "普通" in result
        assert "突袭" not in result

    def test_team_count_display(self):
        """每条记录显示干员人数"""
        result = format_single_record(SAMPLE_RECORD)
        assert "👥 2人" in result

    def test_team_count_empty(self):
        """空队伍显示0人"""
        rec = {**SAMPLE_RECORD, "team": []}
        result = format_single_record(rec)
        assert "👥 0人" in result


# --- format_records 测试 ---

class TestFormatRecords:
    def test_empty_records(self):
        result = format_records([], 0)
        assert len(result) == 1
        assert "没有找到" in result[0]

    def test_single_record(self):
        result = format_records([SAMPLE_RECORD], 1)
        assert len(result) == 1
        assert "H11-1" in result[0]

    def test_multiple_records(self):
        records = [SAMPLE_RECORD, SAMPLE_RECORD]
        result = format_records(records, 2)
        assert len(result) >= 1
        assert "找到最佳记录 2 条" in result[0]

    def test_multiple_records_with_numbering(self):
        records = [SAMPLE_RECORD, SAMPLE_RECORD]
        result = format_records(records, 2)
        full = "".join(result)
        assert "1️⃣" in full
        assert "2️⃣" in full

    def test_count_valid_shown_in_header(self):
        """header 使用 API 返回的 count_valid，不覆盖"""
        records = [SAMPLE_RECORD, SAMPLE_RECORD]
        result = format_records(records, 2)
        assert "找到最佳记录 2 条" in result[0]

    def test_single_record_shows_count(self):
        """单条记录也显示记录人数"""
        result = format_records([SAMPLE_RECORD], 1)
        assert "共 1 条最佳记录" in result[0]

    def test_record_type_list(self):
        result = format_records([SAMPLE_RECORD], 1)
        assert isinstance(result, list)
        assert all(isinstance(m, str) for m in result)

    def test_old_record_filtered_by_group(self):
        """group == '旧纪录' 的记录应被过滤"""
        old_record = {**SAMPLE_RECORD, "group": "旧纪录"}
        result = format_records([old_record], 1)
        assert "没有找到" in result[0]

    def test_mixed_old_and_new_records(self):
        """混合新旧记录时只保留新的（group 为空的），header 用 API 的 count_valid"""
        old_record = {**SAMPLE_RECORD, "group": "旧纪录"}
        new_record = {**SAMPLE_RECORD, "group": ""}
        result = format_records([old_record, new_record], 1)
        assert len(result) == 1
        assert "共 1 条最佳记录" in result[0]
        assert "H11-1" in result[0]

    def test_blank_line_between_records(self):
        """多条记录之间有空行分隔"""
        result = format_records([SAMPLE_RECORD, SAMPLE_RECORD], 2)
        full = result[0]
        # 检查两条记录之间有空行（\n\n 分隔）
        assert "\n\n" in full

    def test_single_record_no_trailing_blank_line(self):
        """单条记录末尾没有多余空行"""
        result = format_records([SAMPLE_RECORD], 1)
        assert not result[0].endswith("\n\n")
