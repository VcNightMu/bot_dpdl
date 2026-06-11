"""resolver/episode_short.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from resolver.episode_short import (
    resolve_episode_short,
    format_episode_choices,
    build_episode_short_map,
    init_episode_short_map,
    _extract_prefix,
    _MAINLINE_MAP,
    _NON_MAINLINE_MAP,
)


# 模拟的 operation_index 数据
SAMPLE_OPERATION_INDEX = {
    "by_operation": {
        # 主线关卡
        "H11-1": {"operation": "H11-1", "cn_name": "惊霆行动-1", "episode": "惊霆无声", "story": "主线关卡", "has_challenge": True},
        "M8-8": {"operation": "M8-8", "cn_name": "破碎", "episode": "破碎日冕", "story": "主线关卡", "has_challenge": True},
        # 非主线关卡 - SV 前缀
        "SV-5": {"operation": "SV-5", "cn_name": "SV-5", "episode": "覆潮之下", "story": "活动关卡", "has_challenge": False},
        "SV-6": {"operation": "SV-6", "cn_name": "SV-6", "episode": "覆潮之下", "story": "活动关卡", "has_challenge": False},
        "SV-7": {"operation": "SV-7", "cn_name": "SV-7", "episode": "乌萨斯的孩子们", "story": "活动关卡", "has_challenge": False},
        # 非主线关卡 - OF 前缀
        "OF-1": {"operation": "OF-1", "cn_name": "OF-1", "episode": "火蓝之心", "story": "活动关卡", "has_challenge": False},
        "OF-2": {"operation": "OF-2", "cn_name": "OF-2", "episode": "火蓝之心", "story": "活动关卡", "has_challenge": False},
        # 非主线关卡 - GT 前缀
        "GT-1": {"operation": "GT-1", "cn_name": "GT-1", "episode": "骑兵与猎人", "story": "活动关卡", "has_challenge": False},
        "GT-EX-1": {"operation": "GT-EX-1", "cn_name": "GT-EX-1", "episode": "骑兵与猎人", "story": "活动关卡", "has_challenge": False},
    },
    "by_cn_name": {},
    "duplicates": {},
}


class TestExtractPrefix:
    def test_simple_prefix(self):
        """测试简单前缀提取"""
        assert _extract_prefix("H11-1") == "H"
        assert _extract_prefix("M8-8") == "M"
        assert _extract_prefix("SV-5") == "SV"
        assert _extract_prefix("OF-1") == "OF"
    
    def test_prefix_with_ex(self):
        """测试带 EX 的前缀"""
        assert _extract_prefix("GT-EX-1") == "GT"
        assert _extract_prefix("CB-EX-1") == "CB"
    
    def test_prefix_with_trailing(self):
        """测试带尾部的前缀"""
        assert _extract_prefix("SV-5A") == "SV"
        assert _extract_prefix("OF-1B") == "OF"
    
    def test_no_prefix(self):
        """测试无前缀"""
        assert _extract_prefix("123") == ""
        assert _extract_prefix("-5") == ""


class TestBuildEpisodeShortMap:
    def test_build_from_index(self):
        """测试从 operation_index 构建映射"""
        result = build_episode_short_map(SAMPLE_OPERATION_INDEX)
        
        # SV 应该对应两个活动
        assert "SV" in result
        assert len(result["SV"]) == 2
        assert "覆潮之下" in result["SV"]
        assert "乌萨斯的孩子们" in result["SV"]
        
        # OF 应该对应一个活动
        assert "OF" in result
        assert result["OF"] == ["火蓝之心"]
        
        # GT 应该对应一个活动
        assert "GT" in result
        assert result["GT"] == ["骑兵与猎人"]
    
    def test_mainline_not_in_map(self):
        """测试主线关卡代号不在映射中"""
        result = build_episode_short_map(SAMPLE_OPERATION_INDEX)
        
        # 主线代号 (H, M 开头) 不应出现在映射中
        assert "H" not in result
        assert "M" not in result
    
    def test_empty_index(self):
        """测试空索引"""
        result = build_episode_short_map({"by_operation": {}})
        assert result == {}


class TestInitEpisodeShortMap:
    def test_init_sets_global(self):
        """测试初始化设置全局映射"""
        import resolver.episode_short as module
        
        # 重置状态
        module._BUILT_FROM_INDEX = False
        module._NON_MAINLINE_MAP = {}
        
        # 初始化
        init_episode_short_map(SAMPLE_OPERATION_INDEX)
        
        # 检查全局映射已设置
        assert module._BUILT_FROM_INDEX is True
        assert "SV" in module._NON_MAINLINE_MAP
        assert "OF" in module._NON_MAINLINE_MAP
    
    def test_init_only_once(self):
        """测试初始化只执行一次"""
        import resolver.episode_short as module
        
        # 重置状态
        module._BUILT_FROM_INDEX = False
        module._NON_MAINLINE_MAP = {}
        
        # 第一次初始化
        init_episode_short_map(SAMPLE_OPERATION_INDEX)
        first_map = module._NON_MAINLINE_MAP.copy()
        
        # 第二次初始化不应改变映射
        init_episode_short_map({"by_operation": {}})
        assert module._NON_MAINLINE_MAP == first_map


class TestResolveEpisodeShort:
    def setup_method(self):
        """每个测试前重新初始化"""
        import resolver.episode_short as module
        module._BUILT_FROM_INDEX = False
        module._NON_MAINLINE_MAP = {}
        init_episode_short_map(SAMPLE_OPERATION_INDEX)
    
    def test_mainline_chapter_format(self):
        """测试主线章节格式: 第X章"""
        result = resolve_episode_short("第五章")
        assert result is not None
        input_text, names = result
        assert input_text == "第五章"
        assert names == ["靶向药物"]
    
    def test_mainline_number_format(self):
        """测试主线章节格式: 纯数字"""
        result = resolve_episode_short("5")
        assert result is not None
        input_text, names = result
        assert input_text == "5"
        assert names == ["靶向药物"]
    
    def test_non_mainline_unique(self):
        """测试非主线活动缩写（唯一匹配）"""
        result = resolve_episode_short("OF")
        assert result is not None
        input_text, names = result
        assert input_text == "OF"
        assert names == ["火蓝之心"]
    
    def test_non_mainline_duplicate(self):
        """测试非主线活动缩写（多个匹配）"""
        result = resolve_episode_short("SV")
        assert result is not None
        input_text, names = result
        assert input_text == "SV"
        assert len(names) == 2
        assert "覆潮之下" in names
        assert "乌萨斯的孩子们" in names
    
    def test_case_insensitive(self):
        """测试非主线缩写大小写不敏感"""
        result_lower = resolve_episode_short("of")
        result_upper = resolve_episode_short("OF")
        result_mixed = resolve_episode_short("Of")
        
        assert result_lower is not None
        assert result_upper is not None
        assert result_mixed is not None
        
        # 结果应该相同
        assert result_lower[1] == result_upper[1] == result_mixed[1]
    
    def test_no_match(self):
        """测试不存在的缩写"""
        result = resolve_episode_short("不存在")
        assert result is None
    
    def test_empty_input(self):
        """测试空输入"""
        assert resolve_episode_short("") is None
        assert resolve_episode_short("   ") is None


class TestFormatEpisodeChoices:
    def test_single_name(self):
        """测试单个活动名"""
        result = format_episode_choices(["火蓝之心"])
        assert result == "火蓝之心"
    
    def test_multiple_names(self):
        """测试多个活动名"""
        result = format_episode_choices(["覆潮之下", "乌萨斯的孩子们"])
        assert "覆潮之下" in result
        assert "乌萨斯的孩子们" in result
        assert "、" in result
    
    def test_custom_cmd_name(self):
        """测试自定义指令名"""
        result = format_episode_choices(["覆潮之下", "乌萨斯的孩子们"], "#待压人")
        assert "#待压人" in result
