# 日期: 2026-06-01
# 开发者: 宝生玛格
# 功能: 视频链接处理模块，B站链接截取BV号，非B站显示"非B站视频"
# 模型: mimo/mimo-v2.5

"""视频链接处理模块

B站链接截取BV号，非B站显示"非B站视频"。
"""
from __future__ import annotations

import re

# BV号正则
_BV_PATTERN = re.compile(r"BV[\w]+")


def extract_bv_number(url: str) -> str | None:
    """从URL中提取BV号

    返回: BV号字符串（如 "BV1xxxxxx"）或 None
    """
    if not url:
        return None
    match = _BV_PATTERN.search(url)
    return match.group(0) if match else None


def format_video_link(url: str) -> str:
    """格式化视频链接

    B站: 显示BV号
    非B站: 显示"非B站视频"
    """
    bv = extract_bv_number(url)
    if bv:
        return bv
    return "非B站视频"
