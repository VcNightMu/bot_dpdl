# -*- coding: utf-8 -*-
# 日期：2026-08-25
# 开发者：橘雪莉
# 功能摘要：resolver/duplicate.py 单元测试 - 关卡代号/中文名重复检测
# 模型：mimo/mimo-v2.5

"""resolver/duplicate.py 单元测试"""

import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from resolver.duplicate import check_duplicate_operation


def _make_index(duplicates=None, cn_name_duplicates=None):
    return {
        "by_operation": {},
        "by_cn_name": {},
        "duplicates": duplicates or {},
        "cn_name_duplicates": cn_name_duplicates or {},
    }


class TestCheckDuplicateOperation:
    def test_operation_duplicate(self):
        """代号重复时提示用中文名"""
        idx = _make_index(duplicates={
            "SV-5": [
                {"operation": "SV-5", "cn_name": "突破口", "episode": "乌萨斯的孩子们"},
                {"operation": "SV-5", "cn_name": "遭弃者", "episode": "覆潮之下"},
            ]
        })
        msg = check_duplicate_operation("SV-5", idx, "#查")
        assert msg is not None
        assert "多个关卡" in msg
        assert "突破口" in msg
        assert "遭弃者" in msg
        assert "中文名" in msg

    def test_annihilation_region_duplicate(self):
        """剿灭地区名重复时提示用中文名"""
        idx = _make_index(duplicates={
            "炎国": [
                {"operation": "炎国", "cn_name": "龙门外环", "episode": "长期委托"},
                {"operation": "炎国", "cn_name": "龙门市区", "episode": "长期委托"},
                {"operation": "炎国", "cn_name": "盘桓蜀道", "episode": "轮换委托"},
            ]
        })
        msg = check_duplicate_operation("炎国", idx, "#查")
        assert msg is not None
        assert "龙门外环" in msg
        assert "龙门市区" in msg
        assert "盘桓蜀道" in msg

    def test_cn_name_duplicate(self):
        """中文名重复时提示用关卡代号"""
        idx = _make_index(cn_name_duplicates={
            "故友重逢": [
                {"operation": "AF-4", "cn_name": "故友重逢", "episode": "洪炉示岁"},
                {"operation": "DH-S-3", "cn_name": "故友重逢", "episode": "多索雷斯假日"},
            ]
        })
        msg = check_duplicate_operation("故友重逢", idx, "#查")
        assert msg is not None
        assert "AF-4" in msg
        assert "DH-S-3" in msg
        assert "关卡代号" in msg

    def test_no_duplicate(self):
        """无重复时返回 None"""
        idx = _make_index()
        assert check_duplicate_operation("H11-1", idx, "#查") is None

    def test_no_index(self):
        """索引为 None 时返回 None"""
        assert check_duplicate_operation("H11-1", None, "#查") is None

    def test_custom_cmd_name(self):
        """自定义指令名出现在提示中"""
        idx = _make_index(duplicates={
            "SV-5": [
                {"operation": "SV-5", "cn_name": "突破口", "episode": "乌萨斯的孩子们"},
                {"operation": "SV-5", "cn_name": "遭弃者", "episode": "覆潮之下"},
            ]
        })
        msg = check_duplicate_operation("SV-5", idx, "#人数")
        assert msg is not None
        assert "#人数" in msg
