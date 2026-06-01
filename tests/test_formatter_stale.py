"""formatter/stale.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from formatter.stale import format_stale, _days_ago


class TestDaysAgo:
    """_days_ago 天数计算测试"""

    def test_past_date(self):
        """过去的日期应返回正数"""
        result = _days_ago("2020-01-01")
        assert result > 0

    def test_today(self):
        """今天的日期应返回0"""
        from datetime import datetime, timezone, timedelta
        cst = timezone(timedelta(hours=8))
        today = datetime.now(cst).strftime("%Y-%m-%d")
        assert _days_ago(today) == 0

    def test_future_date(self):
        """未来日期应返回0（max(0, ...)）"""
        result = _days_ago("2099-12-31")
        assert result == 0

    def test_unknown_format(self):
        assert _days_ago("昨天") == 0

    def test_empty_string(self):
        assert _days_ago("") == 0

    def test_slash_format(self):
        result = _days_ago("2020/01/01")
        assert result > 0


class TestFormatStale:
    def test_empty_stale(self):
        result = format_stale("惊霆无声", "四星队", 365, [])
        assert "无待压人记录" in result

    def test_basic_format(self):
        stale = [
            {
                "operation": "H11-1",
                "cn_name": "惊霆行动-1",
                "difficulty": "challenge",
                "ageDays": 400,
                "records": [{"team": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}], "url": "https://www.bilibili.com/video/BV1test"}],
            }
        ]
        result = format_stale("惊霆无声", "四星队", 365, stale)
        assert "H11-1" in result
        assert "惊霆行动-1" in result
        assert "400天前" in result
        assert "4人" in result
        assert "[突袭]" in result
        assert "BV1test" in result

    def test_normal_difficulty_label(self):
        stale = [
            {
                "operation": "GT-1",
                "cn_name": "打磨利刃",
                "difficulty": "normal",
                "ageDays": 500,
                "records": [{"team": [{"name": "A"}, {"name": "B"}], "url": ""}],
            }
        ]
        result = format_stale("行动", "四星队", 365, stale)
        assert "[普通]" in result

    def test_filter_team_size_1(self):
        """队伍人数为1的应被过滤"""
        stale = [
            {
                "operation": "H11-1",
                "cn_name": "惊霆行动-1",
                "difficulty": "normal",
                "ageDays": 400,
                "records": [{"team": [{"name": "A"}], "url": ""}],
            }
        ]
        result = format_stale("惊霆无声", "四星队", 365, stale)
        assert "无待压人记录" in result

    def test_filter_no_records(self):
        """没有 records 的条目 team_size=0，应被过滤"""
        stale = [
            {
                "operation": "H11-1",
                "cn_name": "惊霆行动-1",
                "difficulty": "normal",
                "ageDays": 400,
                "records": [],
            }
        ]
        result = format_stale("惊霆无声", "四星队", 365, stale)
        assert "无待压人记录" in result

    def test_missing_cn_name(self):
        stale = [
            {
                "operation": "GT-1",
                "difficulty": "normal",
                "ageDays": 400,
                "records": [{"team": [{"name": "A"}, {"name": "B"}], "url": ""}],
            }
        ]
        result = format_stale("行动", "四星队", 365, stale)
        assert "GT-1" in result

    def test_custom_days_in_header(self):
        result = format_stale("ep", "cat", 180, [])
        assert "180天" in result

    def test_is_string(self):
        result = format_stale("ep", "cat", 365, [])
        assert isinstance(result, str)

    def test_non_bilibili_video(self):
        stale = [
            {
                "operation": "GT-1",
                "cn_name": "打磨",
                "difficulty": "normal",
                "ageDays": 400,
                "records": [{"team": [{"name": "A"}, {"name": "B"}], "url": "https://youtube.com/watch?v=abc"}],
            }
        ]
        result = format_stale("ep", "cat", 365, stale)
        assert "非B站视频" in result
