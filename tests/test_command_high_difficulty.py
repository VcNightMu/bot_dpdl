# 日期: 2026-10-10
# 开发者: 橘雪莉
# 功能: #高难 指令单元测试 - 覆盖本地过滤口径、格式化与指令参数解析
# 模型: deepseek-flash


import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""#高难 相关模块单元测试"""

import re
import pytest
from unittest.mock import AsyncMock, patch
from dataclasses import dataclass, field

from resolver.high_difficulty import (
    HIGH_TEAM_THRESHOLD,
    difficulty_label,
    find_high_difficulty,
)
from formatter.high_difficulty import format_high_difficulty
from qq_bot.commands.high_difficulty import handle_high_difficulty
from api_client.models import BotRecord


# --- 构造工具 ---

def rec(operation, size, *, cn_name="测试关", difficulty="normal", url=None, group=""):
    """构造一条 API 原始格式的记录字典，team 长度 = size。"""
    return {
        "operation": operation,
        "cn_name": cn_name,
        "operationType": difficulty,
        "url": url or f"https://www.bilibili.com/video/BV1{operation.replace('-', '')}",
        "team": [{"name": f"干员{i}"} for i in range(size)],
        "group": group,
    }


def bot_record(operation, size, *, cn_name="测试关", difficulty="normal", url=None, group=""):
    """构造一条 api_client.models.BotRecord 对象（生产链路里的真实形态）。"""
    return BotRecord.from_dict({
        "operation": operation,
        "cn_name": cn_name,
        "operationType": difficulty,
        "url": url or f"https://www.bilibili.com/video/BV1{operation.replace('-', '')}",
        "team": [{"name": f"干员{i}"} for i in range(size)],
        "group": group,
    })


def op_index(**has_challenge):
    """构造 operation_index：关键字参数名即关卡代号。"""
    return {
        "by_operation": {
            op.upper().replace("_", "-"): {"has_challenge": hc}
            for op, hc in has_challenge.items()
        }
    }


# ============================================================
# resolver.high_difficulty
# ============================================================

class TestFindHighDifficulty:
    def test_empty_records(self):
        assert find_high_difficulty([]) == []
        assert find_high_difficulty(None) == []

    def test_min_team_size_at_threshold_is_hit(self):
        """最少人正好等于 10 → 命中"""
        hits = find_high_difficulty([rec("H10-3", 10), rec("H10-3", 12)])
        assert len(hits) == 1
        assert hits[0].min_team_size == 10
        assert hits[0].total_records == 2

    def test_below_threshold_excluded(self):
        """最少人 9 → 不命中（即便存在 12 人的记录）"""
        hits = find_high_difficulty([rec("H12-4", 9), rec("H12-4", 12)])
        assert hits == []

    def test_uses_min_not_max(self):
        """一关有 12 人和 4 人记录 → 最少人是 4，不算高难"""
        hits = find_high_difficulty([rec("M8-8", 12), rec("M8-8", 4)])
        assert hits == []

    def test_difficulty_separated(self):
        """普通/突袭独立判定：突袭 12 人命中，普通 3 人不命中"""
        hits = find_high_difficulty([
            rec("BB-S-4", 12, difficulty="challenge"),
            rec("BB-S-4", 3, difficulty="normal"),
        ])
        assert len(hits) == 1
        assert hits[0].difficulty == "challenge"
        assert hits[0].min_team_size == 12

    def test_best_records_only_min_size(self):
        """best_records 只含最少人规模下的记录"""
        hits = find_high_difficulty([
            rec("H10-3", 10, url="https://b.com/video/BV1aaa"),
            rec("H10-3", 10, url="https://b.com/video/BV1bbb"),
            rec("H10-3", 13, url="https://b.com/video/BV1ccc"),
        ])
        assert len(hits[0].best_records) == 2
        assert hits[0].total_records == 3

    def test_records_without_team_ignored(self):
        """没有 team 的脏数据不参与人数统计（否则会被当 0 人最优）"""
        hits = find_high_difficulty([
            {"operation": "H10-3", "cn_name": "测试", "team": []},
            rec("H10-3", 11),
        ])
        assert len(hits) == 1
        assert hits[0].min_team_size == 11

    def test_operation_type_defaults_to_normal(self):
        """缺失 operationType 时按普通处理"""
        r = rec("H10-3", 10)
        del r["operationType"]
        hits = find_high_difficulty([r])
        assert hits[0].difficulty == "normal"

    def test_sorted_by_team_size_desc(self):
        """人数多的（更难的）排前面"""
        hits = find_high_difficulty([
            rec("A-1", 10),
            rec("B-1", 12),
            rec("C-1", 11),
        ])
        assert [h.min_team_size for h in hits] == [12, 11, 10]

    def test_custom_threshold(self):
        hits = find_high_difficulty([rec("H10-3", 8)], threshold=8)
        assert len(hits) == 1

    def test_operation_index_adds_label_when_has_challenge(self):
        hits = find_high_difficulty(
            [rec("BB-S-4", 12, difficulty="challenge")],
            operation_index=op_index(BB_S_4=True),
        )
        assert hits[0].difficulty_label == " [突袭]"

    def test_no_label_when_no_challenge(self):
        """没有突袭的关卡不加 [普通] 标签"""
        hits = find_high_difficulty(
            [rec("TR-22", 10)],
            operation_index=op_index(TR_22=False),
        )
        assert hits[0].difficulty_label == ""


class TestBotRecordObjects:
    """回归：生产链路传进来的是 BotRecord 对象，不是 dict。

    历史 bug：曾用 `dataclasses.asdict()` 把 BotRecord 转成 dict 再交给本模块，
    但 asdict 输出的是 Python 字段名 `operation_type`，而模块读的是
    `operationType` → 难度恒为 None → 普通与突袭被**合并成一组**，
    突袭的 12 人会被普通的 10 人「吃掉」，突袭命中丢失。
    这组测试锁死「对象形态下难度不丢」。
    """

    def test_operation_type_read_from_object(self):
        hits = find_high_difficulty([bot_record("BB-S-4", 10, difficulty="challenge")])
        assert len(hits) == 1
        assert hits[0].difficulty == "challenge"

    def test_challenge_not_merged_into_normal(self):
        """突袭 12 人 + 普通 10 人 → 必须分成两条，且突袭不能被吃掉"""
        hits = find_high_difficulty([
            bot_record("BB-S-4", 12, difficulty="challenge"),
            bot_record("BB-S-4", 10, difficulty="normal"),
        ])
        assert len(hits) == 2
        by_diff = {h.difficulty: h for h in hits}
        assert by_diff["challenge"].min_team_size == 12
        assert by_diff["normal"].min_team_size == 10

    def test_object_and_dict_agree(self):
        """同一批数据的对象形态与 dict 形态结果必须一致。

        这条如果失败，说明又有人引入了有损转换。
        """
        records = [
            ("BB-S-4", 12, "challenge"),
            ("BB-S-4", 10, "normal"),
            ("H10-3", 11, "normal"),
            ("H12-4", 9, "normal"),
        ]
        as_objects = find_high_difficulty(
            [bot_record(op, n, difficulty=d) for op, n, d in records]
        )
        as_dicts = find_high_difficulty(
            [rec(op, n, difficulty=d) for op, n, d in records]
        )
        assert [(h.operation, h.difficulty, h.min_team_size) for h in as_objects] == \
               [(h.operation, h.difficulty, h.min_team_size) for h in as_dicts]

    def test_object_cn_name_and_url_readable(self):
        hits = find_high_difficulty([
            bot_record("BB-S-4", 12, cn_name="模拟刺杀作战-4",
                       url="https://www.bilibili.com/video/BV15RzZYfEjp"),
        ])
        assert hits[0].cn_name == "模拟刺杀作战-4"
        out = format_high_difficulty("巴别塔", "四星队", hits)
        assert "BV15RzZYfEjp" in out


class TestDifficultyLabel:
    def test_none_index_gives_empty(self):
        assert difficulty_label("H10-3", "normal", None) == ""

    def test_unknown_operation_gives_empty(self):
        assert difficulty_label("XXX", "normal", op_index(A_1=True)) == ""

    def test_has_challenge_normal(self):
        assert difficulty_label("BB-S-4", "normal", op_index(BB_S_4=True)) == " [普通]"

    def test_has_challenge_challenge(self):
        assert difficulty_label("BB-S-4", "challenge", op_index(BB_S_4=True)) == " [突袭]"

    def test_case_insensitive_operation(self):
        assert difficulty_label("bb-s-4", "challenge", op_index(BB_S_4=True)) == " [突袭]"


# ============================================================
# formatter.high_difficulty
# ============================================================

class TestFormatHighDifficulty:
    def test_empty_hits(self):
        out = format_high_difficulty("惊霆无声", "四星队", [])
        assert "无高难关卡" in out
        assert "惊霆无声" in out
        assert "四星队" in out

    def test_basic_output(self):
        hits = find_high_difficulty(
            [rec("BB-S-4", 10, cn_name="巴别塔-S-4",
                 url="https://www.bilibili.com/video/BV1xxxxxx")],
            operation_index=op_index(BB_S_4=True),
        )
        out = format_high_difficulty("巴别塔", "四星队", hits)
        assert "💀 巴别塔 · 四星队 高难关卡" in out
        assert "BB-S-4 巴别塔-S-4" in out
        assert "[普通]" in out
        assert "最少 10 人" in out
        assert "共 1 条记录" in out
        assert "BV1xxxxxx" in out

    def test_header_shows_count(self):
        hits = find_high_difficulty([rec("A-1", 10), rec("B-1", 11)])
        out = format_high_difficulty("活动", "四星队", hits)
        assert "2个" in out

    def test_multiple_records_numbered(self):
        hits = find_high_difficulty([
            rec("H10-3", 10, url="https://b.com/video/BV1aaa"),
            rec("H10-3", 10, url="https://b.com/video/BV1bbb"),
        ])
        out = format_high_difficulty("破碎日冕", "四星队", hits)
        assert "1. BV1aaa" in out
        assert "2. BV1bbb" in out

    def test_truncated_note(self):
        hits = find_high_difficulty([rec("H10-3", 11)])
        out = format_high_difficulty("破碎日冕", "四星队", hits, truncated=True)
        assert "结果可能不完整" in out

    def test_long_output_split_into_list(self):
        """超过消息长度上限时拆成多条"""
        records = [rec(f"H10-{i}", 10, url=f"https://b.com/video/BV1{i:06d}") for i in range(1, 40)]
        hits = find_high_difficulty(records)
        out = format_high_difficulty("超大活动", "四星队", hits)
        assert isinstance(out, list)
        assert len(out) > 1
        assert all(len(m) <= 800 for m in out)

    def test_single_message_returns_str(self):
        hits = find_high_difficulty([rec("H10-3", 11)])
        out = format_high_difficulty("破碎日冕", "四星队", hits)
        assert isinstance(out, str)

    def test_non_bilibili_link(self):
        hits = find_high_difficulty([
            rec("H10-3", 10, url="https://www.youtube.com/watch?v=abc"),
        ])
        out = format_high_difficulty("破碎日冕", "四星队", hits)
        assert "非B站视频" in out


# ============================================================
# qq_bot.commands.high_difficulty
# ============================================================

@dataclass
class MockSearchResult:
    """注意：records 用真实的 BotRecord 对象，与生产链路一致。

    原先这里放自定义 dataclass，字段名恰好是 operationType / cn_name，
    因而掩盖了「asdict 转换后 operationType 变 None」的真实 bug。
    """
    count: int = 1
    count_valid: int = 1
    records: list = field(default_factory=lambda: [bot_record("H10-3", 11)])


def make_match(text: str):
    return re.match(r"^#高难\s+(.+)", text)


class TestHandleHighDifficulty:
    @pytest.mark.asyncio
    async def test_missing_category_returns_hint(self):
        match = make_match("#高难 巴别塔")
        result = await handle_high_difficulty(match, group_id=1, user_id=1)
        assert "缺少流派" in result or "流派" in result

    @pytest.mark.asyncio
    async def test_invalid_category_returns_error(self):
        match = make_match("#高难 巴别塔 不存在的流派")
        result = await handle_high_difficulty(match, group_id=1, user_id=1)
        assert "未找到流派" in result or "流派" in result

    @pytest.mark.asyncio
    async def test_calls_api_with_category_and_episode(self):
        match = make_match("#高难 巴别塔 四星队")

        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=MockSearchResult())
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_high_difficulty(match, group_id=1, user_id=1)
            conditions = mock_instance.search_records.call_args[1]["conditions"]
            fields = {c["field"]: c["value"] for c in conditions}
            assert fields["category"] == "四星队"
            assert fields["episode"] == "巴别塔"

    @pytest.mark.asyncio
    async def test_hit_rendered(self):
        match = make_match("#高难 巴别塔 四星队")

        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=MockSearchResult())
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            text = result if isinstance(result, str) else "\n".join(result)
            assert "高难关卡" in text
            assert "H10-3" in text
            assert "11 人" in text

    @pytest.mark.asyncio
    async def test_below_threshold_renders_empty(self):
        """记录最少人 9 → 返回无高难"""
        match = make_match("#高难 惊霆无声 四星队")
        low_result = MockSearchResult(records=[bot_record("12-20", 9)])

        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=low_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            assert "无高难关卡" in result

    @pytest.mark.asyncio
    async def test_challenge_hit_not_lost_end_to_end(self):
        """回归：突袭命中必须出现在最终输出里（不能被普通合并掉）"""
        match = make_match("#高难 巴别塔 四星队")
        result_data = MockSearchResult(count=2, count_valid=2, records=[
            bot_record("BB-S-4", 12, cn_name="模拟刺杀作战-4",
                       difficulty="challenge", url="https://b.com/video/BV1challenge"),
            bot_record("BB-S-4", 10, cn_name="模拟刺杀作战-4",
                       difficulty="normal", url="https://b.com/video/BV1normal"),
        ])

        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=result_data)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            out = await handle_high_difficulty(match, group_id=1, user_id=1)
            text = out if isinstance(out, str) else "\n".join(out)
            assert "最少 12 人" in text, f"突袭命中丢失: {text}"
            assert "BV1challenge" in text
            assert "最少 10 人" in text
            assert "BV1normal" in text

    @pytest.mark.asyncio
    async def test_api_failure_friendly_message(self):
        match = make_match("#高难 巴别塔 四星队")

        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(side_effect=RuntimeError("boom"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            assert "查询失败" in result

    @pytest.mark.asyncio
    async def test_episode_with_space_kept_intact(self):
        """含空格活动名不能被截断"""
        match = make_match("#高难 矢量突破#3 拟生态 四星队")

        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_records = AsyncMock(return_value=MockSearchResult())
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_high_difficulty(match, group_id=1, user_id=1)
            conditions = mock_instance.search_records.call_args[1]["conditions"]
            fields = {c["field"]: c["value"] for c in conditions}
            assert fields["episode"] == "矢量突破#3 拟生态"

    @pytest.mark.asyncio
    async def test_extra_arg_not_silently_dropped(self):
        """末位非数字文本必须明确报错，不能静默丢弃。

        #高难 只接受末尾一个数字，任何非数字 token 都是格式错误。
        """
        match = make_match("#高难 巴别塔 四星队 extra")
        result = await handle_high_difficulty(match, group_id=1, user_id=1)
        assert "应为数字" in result or "无法识别" in result or "无法确定" in result


class TestThreshold:
    """人数阈值参数：0 < 人数 <= 13，省略时默认 10。"""

    @staticmethod
    def _client(records):
        mock_instance = AsyncMock()
        mock_instance.search_records = AsyncMock(
            return_value=MockSearchResult(count=len(records), count_valid=len(records), records=records)
        )
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        return mock_instance

    @pytest.mark.asyncio
    async def test_default_threshold_is_ten(self):
        """不传人数 → 用默认 10，9 人不算高难"""
        match = make_match("#高难 惊霆无声 四星队")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            MockClient.return_value = self._client([bot_record("12-20", 9)])
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            assert "无高难关卡" in result
            assert "10 人" in result

    @pytest.mark.asyncio
    async def test_custom_threshold_lower(self):
        """传 6 → 最少 6 人的关卡应命中（这是精一1级这类基数小的流派要的）"""
        match = make_match("#高难 惊霆无声 精一1级 6")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            MockClient.return_value = self._client([bot_record("12-20", 6)])
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            text = result if isinstance(result, str) else "\n".join(result)
            assert "高难关卡" in text
            assert "最少 6 人" in text
            assert "6 人及以上" in text

    @pytest.mark.asyncio
    async def test_custom_threshold_passed_to_api_flow(self):
        """阈值要真正传进过滤逻辑，不能只是显示"""
        match = make_match("#高难 惊霆无声 四星队 12")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            # 最少 11 人 → 阈值 12 时不该命中
            MockClient.return_value = self._client([bot_record("H12-4", 11)])
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            assert "无高难关卡" in result
            assert "12 人" in result

    @pytest.mark.asyncio
    async def test_threshold_one_is_valid_lower_bound(self):
        """下边界 1 合法（任何有人打的关卡都算）"""
        match = make_match("#高难 惊霆无声 四星队 1")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            MockClient.return_value = self._client([bot_record("12-2", 1)])
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            text = result if isinstance(result, str) else "\n".join(result)
            assert "高难关卡" in text

    @pytest.mark.asyncio
    async def test_threshold_thirteen_is_valid_upper_bound(self):
        """上边界 13 合法（队伍人数上限）"""
        match = make_match("#高难 惊霆无声 四星队 13")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            MockClient.return_value = self._client([bot_record("H12-4", 13)])
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            text = result if isinstance(result, str) else "\n".join(result)
            assert "高难关卡" in text

    @pytest.mark.asyncio
    async def test_threshold_zero_rejected(self):
        """0 不合法（要求 0 < x）"""
        match = make_match("#高难 惊霆无声 四星队 0")
        result = await handle_high_difficulty(match, group_id=1, user_id=1)
        assert "1–13" in result or "1-13" in result

    @pytest.mark.asyncio
    async def test_threshold_fourteen_rejected(self):
        """超过 13 不合法"""
        match = make_match("#高难 惊霆无声 四星队 14")
        result = await handle_high_difficulty(match, group_id=1, user_id=1)
        assert "1–13" in result or "1-13" in result

    @pytest.mark.asyncio
    async def test_threshold_out_of_range_does_not_call_api(self):
        """越界时不该白跑一次 API 调用"""
        match = make_match("#高难 惊霆无声 四星队 99")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = self._client([])
            MockClient.return_value = mock_instance
            await handle_high_difficulty(match, group_id=1, user_id=1)
            mock_instance.search_records.assert_not_called()

    @pytest.mark.asyncio
    async def test_threshold_with_space_episode(self):
        """含空格活动名 + 人数阈值 同时出现也要正确切分"""
        match = make_match("#高难 矢量突破#3 拟生态 四星队 8")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            mock_instance = self._client([bot_record("BB-1", 8)])
            MockClient.return_value = mock_instance
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            conditions = mock_instance.search_records.call_args[1]["conditions"]
            fields = {c["field"]: c["value"] for c in conditions}
            assert fields["episode"] == "矢量突破#3 拟生态"
            assert fields["category"] == "四星队"
            text = result if isinstance(result, str) else "\n".join(result)
            assert "最少 8 人" in text

    @pytest.mark.asyncio
    async def test_days_suffix_still_accepted(self):
        """兼容 "6天" 这种写法（与 #待压人 的解析保持一致）"""
        match = make_match("#高难 惊霆无声 四星队 6天")
        with patch("qq_bot.commands.high_difficulty.WikiClient") as MockClient:
            MockClient.return_value = self._client([bot_record("12-20", 6)])
            result = await handle_high_difficulty(match, group_id=1, user_id=1)
            text = result if isinstance(result, str) else "\n".join(result)
            assert "最少 6 人" in text


# ============================================================
# handler 路由
# ============================================================

class TestHandlerRouting:
    def test_high_difficulty_registered(self):
        from qq_bot.handler import CommandHandler
        handler = CommandHandler()
        patterns = [p.pattern for p, _ in handler.commands]
        assert r"^#高难\s+(.+)" in patterns
        assert r"^#高难\s*$" in patterns

    @pytest.mark.asyncio
    async def test_no_args_returns_usage(self):
        from qq_bot.handler import CommandHandler
        handler = CommandHandler()
        result = await handler.handle("#高难", group_id=1, user_id=1)
        assert "缺少参数" in result
        assert "#高难 <活动名> <流派>" in result

    @pytest.mark.asyncio
    async def test_trailing_space_still_matches(self):
        from qq_bot.handler import CommandHandler
        handler = CommandHandler()
        result = await handler.handle("#高难 ", group_id=1, user_id=1)
        assert "缺少参数" in result

    def test_help_lists_high_difficulty(self):
        from formatter.help import format_help
        assert "#高难 <活动名> <流派>" in format_help()
    def test_threshold_is_ten(self):
        assert HIGH_TEAM_THRESHOLD == 10
