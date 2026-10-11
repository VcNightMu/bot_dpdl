# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: stale.py 单元测试 - 验证 #待压人 指令的参数解析和API调用
# 模型: mimo/mimo-v2.5


import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""qq_bot/commands/stale.py 单元测试"""

import sys
import re
import pytest
from unittest.mock import AsyncMock, patch
from dataclasses import dataclass, field

pass  # 仓库根已由 _REPO_ROOT 注入 sys.path

from qq_bot.commands.stale import handle_stale


# --- Mock 数据 ---

@dataclass
class MockStaleRecord:
    operation: str = "12-10"
    cn_name: str = "广播热线正繁忙"
    operation_type: str = "challenge"
    age_days: int = 1151
    records: list = field(default_factory=lambda: [
        {"team": [{"name": "红云", "skillStr": "2"}], "url": "https://bilibili.com/video/BV1xxx"}
    ])


@dataclass
class MockStaleResult:
    episode: str = "惊霆无声"
    category: str = "四星队"
    days: int = 365
    stale: list = field(default_factory=lambda: [MockStaleRecord()])


def make_match(text: str):
    """创建正则匹配对象"""
    return re.match(r"^#待压人\s+(.+)", text)


def _stale_item(operation: str, cn_name: str) -> dict:
    """构造一个待压人条目（dict，贴近真实 API 返回）"""
    return {
        "operation": operation,
        "cn_name": cn_name,
        "difficulty": "normal",
        "ageDays": 100,
        "records": [
            {
                "team": [{"name": "红云", "skillStr": "2"}, {"name": "黑角", "skillStr": "1"}],
                "url": "https://bilibili.com/video/BV1xxx",
            }
        ],
    }


class TestHandleStale:
    """测试 handle_stale"""

    @pytest.mark.asyncio
    async def test_missing_category_returns_hint(self):
        """缺少流派参数时返回提示"""
        match = make_match("#待压人 惊霆无声")
        result = await handle_stale(match, group_id=1, user_id=1)
        assert "缺少流派" in result or "流派" in result

    @pytest.mark.asyncio
    async def test_invalid_category_returns_error(self):
        """无效流派名返回错误提示"""
        match = make_match("#待压人 惊霆无声 不存在的流派")
        with patch("resolver.command_args.normalize_category", return_value=None):
            result = await handle_stale(match, group_id=1, user_id=1)
            assert "未找到流派" in result

    @pytest.mark.asyncio
    async def test_invalid_days_returns_error(self):
        """天数格式错误返回提示（用真实流派解析，不 mock）"""
        match = make_match("#待压人 惊霆无声 四星队 abc")
        result = await handle_stale(match, group_id=1, user_id=1)
        assert "天数格式错误" in result or "数字" in result

    @pytest.mark.asyncio
    async def test_episode_name_with_space(self):
        """活动名含空格（线上真实存在「矢量突破#3 拟生态」）"""
        match = make_match("#待压人 矢量突破#3 拟生态 四星队")
        mock_result = MockStaleResult()

        with patch("qq_bot.commands.stale.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_stale(match, group_id=1, user_id=1)
            call_kwargs = mock_instance.stale_records.call_args[1]
            # 活动名必须完整保留，不能被截断成 "矢量突破#3"
            assert call_kwargs["episode"] == "矢量突破#3 拟生态"
            assert call_kwargs["category"] == "四星队"

    @pytest.mark.asyncio
    async def test_days_with_tian_suffix(self):
        """天数写成 "180天" 也应正确解析"""
        match = make_match("#待压人 惊霆无声 四星队 180天")
        mock_result = MockStaleResult(days=180)

        with patch("qq_bot.commands.stale.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            await handle_stale(match, group_id=1, user_id=1)
            assert mock_instance.stale_records.call_args[1]["days"] == 180

    @pytest.mark.asyncio
    async def test_extra_arg_not_silently_dropped(self):
        """多余参数要明确报错，不能静默丢弃"""
        match = make_match("#待压人 惊霆无声 四星队 180 extra")
        result = await handle_stale(match, group_id=1, user_id=1)
        assert "应为数字" in result or "无法识别" in result

    @pytest.mark.asyncio
    async def test_custom_days(self):
        """自定义天数参数"""
        match = make_match("#待压人 惊霆无声 四星队 180")
        mock_result = MockStaleResult(days=180)

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.stale.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_stale(match, group_id=1, user_id=1)
            # 验证调用了 API 且天数为 180
            call_kwargs = mock_instance.stale_records.call_args[1]
            assert call_kwargs["days"] == 180

    @pytest.mark.asyncio
    async def test_default_days(self):
        """不传天数时使用默认值 365"""
        match = make_match("#待压人 惊霆无声 四星队")
        mock_result = MockStaleResult()

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.stale.config") as mock_config:
            mock_config.default_stale_days = 365
            with patch("qq_bot.commands.stale.WikiClient") as MockClient:
                mock_instance = AsyncMock()
                mock_instance.stale_records = AsyncMock(return_value=mock_result)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=False)
                MockClient.return_value = mock_instance

                result = await handle_stale(match, group_id=1, user_id=1)
                call_kwargs = mock_instance.stale_records.call_args[1]
                assert call_kwargs["days"] == 365

    @pytest.mark.asyncio
    async def test_api_error_returns_fallback(self):
        """API 异常时返回错误提示"""
        match = make_match("#待压人 惊霆无声 四星队")

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.stale.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(side_effect=Exception("API 超时"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_stale(match, group_id=1, user_id=1)
            assert "失败" in result or "重试" in result

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """正常查询返回格式化结果"""
        match = make_match("#待压人 惊霆无声 四星队")
        mock_result = MockStaleResult()

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.stale.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(return_value=mock_result)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_stale(match, group_id=1, user_id=1)
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_aggregate_annihilation_query(self):
        """聚合查询：剿灭 → 分别查长期委托+轮换委托并合并"""
        match = make_match("#待压人 剿灭 四星队")
        mock_result_1 = MockStaleResult(stale=[
            _stale_item("乌萨斯", "切尔诺伯格")
        ])
        mock_result_2 = MockStaleResult(stale=[
            _stale_item("玻利瓦尔", "多索雷斯换水口")
        ])

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.stale.WikiClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(side_effect=[mock_result_1, mock_result_2])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            result = await handle_stale(match, group_id=1, user_id=1)

            assert mock_instance.stale_records.call_count == 2
            assert "切尔诺伯格" in result
            assert "多索雷斯换水口" in result

    @pytest.mark.asyncio
    async def test_aggregate_dedup(self):
        """聚合查询去重：跨episode重复的关卡只保留一次"""
        match = make_match("#待压人 剿灭 四星队")
        mock_result_1 = MockStaleResult(stale=[
            _stale_item("乌萨斯", "切尔诺伯格")
        ])
        mock_result_2 = MockStaleResult(stale=[
            _stale_item("乌萨斯", "切尔诺伯格"),
            _stale_item("玻利瓦尔", "多索雷斯换水口")
        ])

        with patch("resolver.command_args.normalize_category", return_value="四星队"), \
             patch("qq_bot.commands.stale.WikiClient") as MockClient, \
             patch("qq_bot.commands.stale.format_stale") as mock_fmt:
            mock_instance = AsyncMock()
            mock_instance.stale_records = AsyncMock(side_effect=[mock_result_1, mock_result_2])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance
            mock_fmt.return_value = "formatted"

            await handle_stale(match, group_id=1, user_id=1)

            stale_arg = mock_fmt.call_args[0][3]
            assert len(stale_arg) == 2
