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

from qq_bot.commands.uncleared import handle_uncleared, filter_uncleared


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
        with patch("resolver.command_args.normalize_category", return_value=None):
            result = await handle_uncleared(match, group_id=1, user_id=1)
            assert "未找到流派" in result

    @pytest.mark.asyncio
    async def test_episode_name_with_space(self):
        """活动名含空格（线上真实存在「矢量突破#2 巫术之夜」）"""
        match = make_match("#未通关 矢量突破#2 巫术之夜 四星队")
        mock_result = MockUnclearedResult()

        with patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_uncleared(match, group_id=1, user_id=1)
            call_kwargs = mock_instance.uncleared.call_args[1]
            assert call_kwargs["episode"] == "矢量突破#2 巫术之夜"
            assert call_kwargs["category"] == "四星队"

    @pytest.mark.asyncio
    async def test_extra_arg_not_silently_dropped(self):
        """多余参数要明确报错，不能静默丢弃"""
        match = make_match("#未通关 惊霆无声 四星队 extra")
        result = await handle_uncleared(match, group_id=1, user_id=1)
        assert "无法识别" in result or "格式错误" in result

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """正常查询返回格式化结果"""
        match = make_match("#未通关 惊霆无声 四星队")
        mock_result = MockUnclearedResult()

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(return_value=mock_result)
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

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
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

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
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

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient, \
             patch("qq_bot.commands.uncleared.format_uncleared") as mock_fmt:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance
            mock_fmt.return_value = "formatted result"

            result = await handle_uncleared(match, group_id=1, user_id=2, operation_index=test_index)
            call_args = mock_fmt.call_args
            assert call_args[0][3] is test_index

    @pytest.mark.asyncio
    async def test_aggregate_annihilation_query(self):
        """聚合查询：剿灭 → 分别查长期委托+轮换委托并合并"""
        match = make_match("#未通关 剿灭 四星队")
        mock_result_1 = MockUnclearedResult(episode="长期委托", uncleared=[
            {"operation": "乌萨斯", "cn_name": "切尔诺伯格", "difficulty": "normal"}
        ])
        mock_result_2 = MockUnclearedResult(episode="轮换委托", uncleared=[
            {"operation": "玻利瓦尔", "cn_name": "多索雷斯换水口", "difficulty": "normal"}
        ])

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(side_effect=[mock_result_1, mock_result_2])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_uncleared(match, group_id=1, user_id=1)

            assert mock_instance.uncleared.call_count == 2
            assert "切尔诺伯格" in result
            assert "多索雷斯换水口" in result

    @pytest.mark.asyncio
    async def test_aggregate_dedup(self):
        """聚合查询去重：跨episode重复的关卡只保留一次"""
        match = make_match("#未通关 剿灭 四星队")
        mock_result_1 = MockUnclearedResult(uncleared=[
            {"operation": "乌萨斯", "cn_name": "切尔诺伯格", "difficulty": "normal"}
        ])
        mock_result_2 = MockUnclearedResult(uncleared=[
            {"operation": "乌萨斯", "cn_name": "切尔诺伯格", "difficulty": "normal"},
            {"operation": "玻利瓦尔", "cn_name": "多索雷斯换水口", "difficulty": "normal"}
        ])

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.uncleared.WikiClient") as MockClient, \
             patch("qq_bot.commands.uncleared.format_uncleared") as mock_fmt:
            mock_instance = AsyncMock()
            mock_instance.uncleared = AsyncMock(side_effect=[mock_result_1, mock_result_2])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance
            mock_fmt.return_value = "formatted"

            await handle_uncleared(match, group_id=1, user_id=1)

            uncleared_arg = mock_fmt.call_args[0][2]
            assert len(uncleared_arg) == 2


class TestFilterUncleared:
    """测试 filter_uncleared - 突袭等效普通过滤"""

    def test_only_normal_with_challenge_removed(self):
        """has_challenge=True，只有normal → 去掉"""
        uncleared = [
            {"operation": "17-10", "cn_name": "裂变临界", "difficulty": "normal"},
        ]
        op_index = {"by_operation": {"17-10": {"has_challenge": True}}}
        result = filter_uncleared(uncleared, op_index)
        assert len(result) == 0

    def test_only_challenge_kept(self):
        """has_challenge=True，只有challenge → 保留"""
        uncleared = [
            {"operation": "17-10", "cn_name": "裂变临界", "difficulty": "challenge"},
        ]
        op_index = {"by_operation": {"17-10": {"has_challenge": True}}}
        result = filter_uncleared(uncleared, op_index)
        assert len(result) == 1
        assert result[0]["difficulty"] == "challenge"

    def test_both_kept(self):
        """has_challenge=True，两个都有 → 保留两条"""
        uncleared = [
            {"operation": "17-10", "cn_name": "裂变临界", "difficulty": "challenge"},
            {"operation": "17-10", "cn_name": "裂变临界", "difficulty": "normal"},
        ]
        op_index = {"by_operation": {"17-10": {"has_challenge": True}}}
        result = filter_uncleared(uncleared, op_index)
        assert len(result) == 2

    def test_no_challenge_mode_not_filtered(self):
        """has_challenge=False → 不过滤"""
        uncleared = [
            {"operation": "GT-1", "cn_name": "打磨利刃", "difficulty": "normal"},
        ]
        op_index = {"by_operation": {"GT-1": {"has_challenge": False}}}
        result = filter_uncleared(uncleared, op_index)
        assert len(result) == 1

    def test_no_operation_index_passthrough(self):
        """没有operation_index → 原样返回"""
        uncleared = [
            {"operation": "17-10", "difficulty": "normal"},
        ]
        result = filter_uncleared(uncleared, None)
        assert len(result) == 1

    def test_mixed_stages(self):
        """混合场景：一个被过滤，一个保留"""
        uncleared = [
            {"operation": "17-10", "cn_name": "裂变临界", "difficulty": "normal"},
            {"operation": "17-11", "cn_name": "归程信号", "difficulty": "challenge"},
            {"operation": "TR-28", "cn_name": "人权宣言", "difficulty": "normal"},
        ]
        op_index = {
            "by_operation": {
                "17-10": {"has_challenge": True},
                "17-11": {"has_challenge": True},
                "TR-28": {"has_challenge": False},
            }
        }
        result = filter_uncleared(uncleared, op_index)
        ops = [(item["operation"], item["difficulty"]) for item in result]
        assert ("17-10", "normal") not in ops  # 被过滤
        assert ("17-11", "challenge") in ops   # 保留
        assert ("TR-28", "normal") in ops      # 无突袭，保留
