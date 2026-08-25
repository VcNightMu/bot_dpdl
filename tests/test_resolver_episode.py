"""resolver/episode.py 单元测试"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

import pytest
from resolver.episode import resolve_episode, build_episode_index, resolve_aggregate_episodes, AGGREGATE_EPISODES


SAMPLE_MENU = [
    {
        "story": "活动关卡",
        "episodes": [
            {
                "episode": "惊霆无声",
                "operations": [
                    {"operation": "H11-1", "cn_name": "惊霆行动-1", "hasChallenge": True},
                ],
            },
            {
                "episode": "破碎日冕",
                "operations": [
                    {"operation": "M8-8", "cn_name": "破碎", "hasChallenge": True},
                ],
            },
        ],
    }
]


class TestBuildEpisodeIndex:
    def test_build_index(self):
        idx = build_episode_index(SAMPLE_MENU)
        assert "惊霆无声" in idx
        assert idx["惊霆无声"]["story"] == "活动关卡"
        assert len(idx["惊霆无声"]["operations"]) == 1

    def test_multiple_episodes(self):
        idx = build_episode_index(SAMPLE_MENU)
        assert len(idx) == 2

    def test_empty_menu(self):
        idx = build_episode_index([])
        assert idx == {}


class TestResolveEpisode:
    def setup_method(self):
        self.idx = build_episode_index(SAMPLE_MENU)

    def test_exact_match(self):
        result = resolve_episode("惊霆无声", self.idx)
        assert result is not None
        assert result["episode"] == "惊霆无声"

    def test_no_match(self):
        assert resolve_episode("不存在的活动", self.idx) is None

    def test_empty_input(self):
        assert resolve_episode("", self.idx) is None

    def test_whitespace_input(self):
        assert resolve_episode("   ", self.idx) is None

    def test_partial_match_rejected(self):
        assert resolve_episode("惊霆", self.idx) is None

    def test_case_sensitive(self):
        assert resolve_episode("惊霆无声", self.idx) is not None
        assert resolve_episode("惊霆無聲", self.idx) is None


class TestResolveAggregateEpisodes:
    def test_annihilation_alias(self):
        """"剿灭"返回长期委托+轮换委托"""
        result = resolve_aggregate_episodes("剿灭")
        assert result is not None
        assert result == ["长期委托", "轮换委托"]

    def test_full_name_alias(self):
        """"剿灭作战"同样返回两个 episode"""
        result = resolve_aggregate_episodes("剿灭作战")
        assert result == ["长期委托", "轮换委托"]

    def test_normal_episode_not_aggregate(self):
        """普通活动名不触发聚合"""
        assert resolve_aggregate_episodes("火蓝之心") is None
        assert resolve_aggregate_episodes("长期委托") is None
        assert resolve_aggregate_episodes("轮换委托") is None

    def test_empty_input(self):
        assert resolve_aggregate_episodes("") is None
        assert resolve_aggregate_episodes("   ") is None

    def test_aggregate_map_contains_both_aliases(self):
        """聚合映射里两个别名指向同一组 episode"""
        assert AGGREGATE_EPISODES["剿灭"] == AGGREGATE_EPISODES["剿灭作战"]
