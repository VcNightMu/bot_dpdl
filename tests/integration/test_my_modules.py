"""测试我负责的模块：resolver + formatter"""
import sys
sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from resolver.operation import normalize_operation, resolve_operation, build_operation_index
from resolver.episode import resolve_episode, build_episode_index
from resolver.category import normalize_category, CATEGORIES
from formatter.video import extract_bv_number, format_video_link
from formatter.record import format_single_record, format_records
from formatter.uncleared import format_uncleared
from formatter.stale import format_stale
from formatter.category import format_categories
from formatter.help import format_help


# ====== resolver 测试 ======

def test_normalize_operation():
    assert normalize_operation("M8-8") == "M8-8"
    assert normalize_operation("m8-8") == "M8-8"
    assert normalize_operation("M8 8") == "M8-8"
    assert normalize_operation("h11-1") == "H11-1"
    assert normalize_operation("gt ex1") == "GT-EX-1"
    print("✅ normalize_operation 通过")


def test_resolve_operation():
    # 模拟 menu_index
    idx = {
        "by_operation": {
            "M8-8": {"operation": "M8-8", "cn_name": "破碎日冕", "episode": "活动", "has_challenge": True},
            "H11-1": {"operation": "H11-1", "cn_name": "惊霆行动-1", "episode": "惊霆无声", "has_challenge": True},
        },
        "by_cn_name": {
            "破碎日冕": {"operation": "M8-8", "cn_name": "破碎日冕", "episode": "活动", "has_challenge": True},
            "惊霆行动-1": {"operation": "H11-1", "cn_name": "惊霆行动-1", "episode": "惊霆无声", "has_challenge": True},
        }
    }

    # 按代号匹配
    r = resolve_operation("M8-8", idx)
    assert r is not None
    assert r[0]["operation"] == "M8-8"
    assert r[1] == "operation"

    # 大小写不敏感
    r = resolve_operation("m8-8", idx)
    assert r is not None
    assert r[0]["operation"] == "M8-8"

    # 按中文名匹配
    r = resolve_operation("惊霆行动-1", idx)
    assert r is not None
    assert r[0]["cn_name"] == "惊霆行动-1"
    assert r[1] == "cn_name"

    # 不存在
    r = resolve_operation("不存在", idx)
    assert r is None

    print("✅ resolve_operation 通过")


def test_resolve_episode():
    idx = {
        "惊霆无声": {"story": "活动关卡", "episode": "惊霆无声", "operations": []},
    }
    assert resolve_episode("惊霆无声", idx) is not None
    assert resolve_episode("不存在", idx) is None
    print("✅ resolve_episode 通过")


def test_normalize_category():
    assert normalize_category("四星队") == "四星队"
    assert normalize_category("四星") == "四星队"
    assert normalize_category("4星") == "四星队"
    assert normalize_category("精一满级") == "精一满级四星队"
    assert normalize_category("三星") == "三星队"
    assert normalize_category("无精英") == "无精英满级"
    assert normalize_category("不存在") is None
    print("✅ normalize_category 通过")


# ====== formatter 测试 ======

def test_video():
    assert extract_bv_number("https://www.bilibili.com/video/BV1xxxxxx") == "BV1xxxxxx"
    assert extract_bv_number("https://www.youtube.com/watch?v=abc") is None
    assert extract_bv_number("") is None
    assert format_video_link("https://www.bilibili.com/video/BV1xxxxxx") == "BV1xxxxxx"
    assert format_video_link("https://www.youtube.com/watch?v=abc") == "非B站视频"
    print("✅ video 通过")


def test_format_single_record():
    record = {
        "operation": "H11-1",
        "cn_name": "惊霆行动-1",
        "operation_type": "challenge",
        "category": ["四星队"],
        "raider": "玩家A",
        "team": [
            {"name": "司霆惊蛰", "skillStr": "1"},
            {"name": "黑角", "skillStr": "1"},
        ],
        "date_published": "2024-09-01",
        "url": "https://www.bilibili.com/video/BV1test",
    }
    result = format_single_record(record, 1)
    assert "H11-1" in result
    assert "惊霆行动-1" in result
    assert "突袭" in result
    assert "BV1test" in result
    assert "司霆惊蛰(1)" in result
    print("✅ format_single_record 通过")


def test_format_records_empty():
    msgs = format_records([], 0)
    assert "没有找到" in msgs[0]
    print("✅ format_records empty 通过")


def test_format_records_single():
    records = [{"operation": "M8-8", "cn_name": "破碎日冕", "operation_type": "normal",
                "category": ["四星队"], "raider": "玩家B", "team": [],
                "date_published": "2025-01-01", "url": "https://bilibili.com/video/BV1a"}]
    msgs = format_records(records, 1)
    assert len(msgs) == 1
    assert "M8-8" in msgs[0]
    print("✅ format_records single 通过")


def test_format_uncleared():
    uncleared = [
        {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge"},
        {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal"},
    ]
    # 带 operation_index（has_challenge=True）
    op_index = {"by_operation": {"H11-1": {"has_challenge": True}}}
    result = format_uncleared("惊霆无声", "四星队", uncleared, op_index)
    assert "惊霆无声" in result
    assert "2个" in result
    assert "[突袭]" in result
    assert "[普通]" in result
    print("✅ format_uncleared 通过")


def test_format_stale():
    stale = [
        {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge",
         "team_size": 4, "latest_date": "2024-09-01", "latest_url": "https://bilibili.com/video/BV1xxx"},
    ]
    result = format_stale("惊霆无声", "四星队", 365, stale)
    assert "惊霆无声" in result
    assert "4人" in result
    assert "BV1xxx" in result
    print("✅ format_stale 通过")


def test_format_stale_filter_size1():
    """队伍人数为1的应被过滤"""
    stale = [
        {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal",
         "team_size": 1, "latest_date": "2024-09-01", "latest_url": ""},
    ]
    result = format_stale("惊霆无声", "四星队", 365, stale)
    assert "无待压人记录" in result
    print("✅ format_stale filter size1 通过")


def test_format_categories():
    result = format_categories()
    assert "四星队" in result
    assert "无精英1级" in result
    print("✅ format_categories 通过")


def test_format_help():
    result = format_help()
    assert "#查" in result
    assert "#help" in result
    print("✅ format_help 通过")


if __name__ == "__main__":
    test_normalize_operation()
    test_resolve_operation()
    test_resolve_episode()
    test_normalize_category()
    test_video()
    test_format_single_record()
    test_format_records_empty()
    test_format_records_single()
    test_format_uncleared()
    test_format_stale()
    test_format_stale_filter_size1()
    test_format_categories()
    test_format_help()
    print("\n🎉 所有测试通过")
