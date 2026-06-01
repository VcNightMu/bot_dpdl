"""formatter/video.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from formatter.video import extract_bv_number, format_video_link


class TestExtractBvNumber:
    """extract_bv_number BV号提取测试"""

    def test_standard_bilibili_url(self):
        url = "https://www.bilibili.com/video/BV1GJ411x7h7"
        assert extract_bv_number(url) == "BV1GJ411x7h7"

    def test_bv_in_long_url(self):
        url = "https://www.bilibili.com/video/BV1xxxxxx?spm_id_from=333.337.0.0"
        assert extract_bv_number(url) == "BV1xxxxxx"

    def test_bv_no_suffix(self):
        url = "BV1234567"
        assert extract_bv_number(url) == "BV1234567"

    def test_bv_with_underscores(self):
        url = "BV1_a_b_c"
        assert extract_bv_number(url) == "BV1_a_b_c"

    def test_no_bv_in_url(self):
        url = "https://www.youtube.com/watch?v=abc123"
        assert extract_bv_number(url) is None

    def test_empty_string(self):
        assert extract_bv_number("") is None

    def test_none_like_empty(self):
        assert extract_bv_number("") is None

    def test_bv_at_end(self):
        url = "https://example.com/BV1test"
        assert extract_bv_number(url) == "BV1test"

    def test_bv_in_middle(self):
        url = "prefix BV1xxx suffix"
        assert extract_bv_number(url) == "BV1xxx"

    def test_lowercase_bv_not_matched(self):
        r"""bv小写不匹配正则 BV[\w]+"""
        url = "https://www.bilibili.com/video/bv1234567"
        assert extract_bv_number(url) is None


class TestFormatVideoLink:
    """format_video_link 视频链接格式化测试"""

    def test_bilibili_url(self):
        url = "https://www.bilibili.com/video/BV1GJ411x7h7"
        assert format_video_link(url) == "BV1GJ411x7h7"

    def test_non_bilibili_url(self):
        url = "https://www.youtube.com/watch?v=abc"
        assert format_video_link(url) == "非B站视频"

    def test_empty_url(self):
        assert format_video_link("") == "非B站视频"

    def test_douyin_url(self):
        url = "https://www.douyin.com/video/123456"
        assert format_video_link(url) == "非B站视频"

    def test_bv_only_string(self):
        assert format_video_link("BV1test") == "BV1test"
