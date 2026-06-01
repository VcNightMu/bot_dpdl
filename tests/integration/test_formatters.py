"""
展示格式验证测试 - 远野汉娜
验证格式化输出是否符合技术方案第八章
"""
import sys
import io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入格式化模块
from formatter.record import format_single_record, format_records
from formatter.help import format_help
from formatter.category import format_categories
from formatter.stale import format_stale
from formatter.uncleared import format_uncleared

# 测试结果存储
test_results = []

def log_test(case_id, name, status, actual="", expected="", notes=""):
    """记录测试结果"""
    result = {
        "case_id": case_id,
        "name": name,
        "status": status,
        "actual": actual,
        "expected": expected,
        "notes": notes,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_icon} [{case_id}] {name}")
    if status == "FAIL":
        print(f"   预期: {expected}")
        print(f"   实际: {actual}")
        if notes:
            print(f"   备注: {notes}")

def test_record_format():
    """测试 #查 记录格式"""
    print("\n" + "=" * 60)
    print("展示格式验证测试")
    print("=" * 60)
    
    # FMT-001: 单条记录格式
    record = {
        "operation": "H11-1",
        "cn_name": "惊霆行动-1",
        "operation_type": "normal",
        "category": ["四星队"],
        "raider": "测试玩家",
        "team": [
            {"name": "司霆惊蛰", "skillStr": "1"},
            {"name": "黑角", "skillStr": "1"}
        ],
        "date_published": "2024-09-01T12:00:00.000Z",
        "url": "https://www.bilibili.com/video/BV1xx411c7mD"
    }
    
    result = format_single_record(record)
    print("单条记录格式示例:")
    print(result)
    
    # 验证格式
    checks = [
        ("📋 关卡代号", "📋" in result),
        ("中文名", "惊霆行动-1" in result),
        ("难度标签", "普通" in result),
        ("🏷️ 流派", "🏷️" in result and "四星队" in result),
        ("👤 玩家名", "👤" in result and "测试玩家" in result),
        ("👥 干员列表", "👥" in result and "司霆惊蛰(1)" in result),
        ("📅 日期", "📅" in result and "2024-09-01" in result),
        ("🔗 BV号", "🔗" in result and "BV1xx411c7mD" in result),
    ]
    
    for check_name, passed in checks:
        if passed:
            log_test("FMT-001", f"单条记录-{check_name}", "PASS")
        else:
            log_test("FMT-001", f"单条记录-{check_name}", "FAIL",
                    result[:100], f"包含{check_name}")

    # FMT-002: 多条记录格式
    records = [record, record]
    messages = format_records(records, 2)
    if len(messages) > 0 and "找到最佳记录 2 条" in messages[0]:
        log_test("FMT-002", "多条记录-标题", "PASS")
    else:
        log_test("FMT-002", "多条记录-标题", "FAIL",
                messages[0][:100] if messages else "空", "包含'找到最佳记录 2 条'")

    # FMT-003: 空记录格式
    messages = format_records([], 0)
    if len(messages) == 1 and "没有找到最佳记录" in messages[0]:
        log_test("FMT-003", "空记录格式", "PASS")
    else:
        log_test("FMT-003", "空记录格式", "FAIL",
                messages[0][:100] if messages else "空", "包含'没有找到最佳记录'")

    # FMT-004: 突袭难度标签
    record_challenge = record.copy()
    record_challenge["operation_type"] = "challenge"
    result = format_single_record(record_challenge)
    if "突袭" in result:
        log_test("FMT-004", "突袭难度标签", "PASS")
    else:
        log_test("FMT-004", "突袭难度标签", "FAIL",
                result[:100], "包含'突袭'")

    # FMT-005: 多流派显示
    record_multi_cat = record.copy()
    record_multi_cat["category"] = ["四星队", "精一满级四星队"]
    result = format_single_record(record_multi_cat)
    if "四星队 / 精一满级四星队" in result:
        log_test("FMT-005", "多流派显示", "PASS")
    else:
        log_test("FMT-005", "多流派显示", "FAIL",
                result[:100], "包含'四星队 / 精一满级四星队'")

def test_help_format():
    """测试 #help 格式"""
    result = format_help()
    print("\n--- #help 格式 ---")
    print(result)
    
    checks = [
        ("标题", "📋" in result and "少人WIKI" in result),
        ("#查指令", "#查" in result and "<关卡> <流派>" in result),
        ("#未通关指令", "#未通关" in result),
        ("#待压人指令", "#待压人" in result),
        ("#流派指令", "#流派" in result),
        ("#help指令", "#help" in result),
        ("示例", "示例" in result and "#查 H11-1 四星队" in result),
    ]
    
    for check_name, passed in checks:
        if passed:
            log_test("FMT-050", f"help-{check_name}", "PASS")
        else:
            log_test("FMT-050", f"help-{check_name}", "FAIL",
                    result[:100], f"包含{check_name}")

def test_category_format():
    """测试 #流派 格式"""
    result = format_categories()
    print("\n--- #流派 格式 ---")
    print(result)
    
    checks = [
        ("标题", "🏷️" in result and "所有流派" in result),
        ("四星队", "四星队" in result),
        ("精一满级四星队", "精一满级四星队" in result),
        ("精一1级四星队", "精一1级四星队" in result),
        ("三星队", "三星队" in result),
        ("精一1级", "精一1级" in result),
        ("无精英满级", "无精英满级" in result),
        ("无精英1级", "无精英1级" in result),
    ]
    
    for check_name, passed in checks:
        if passed:
            log_test("FMT-040", f"流派-{check_name}", "PASS")
        else:
            log_test("FMT-040", f"流派-{check_name}", "FAIL",
                    result[:100], f"包含{check_name}")

def test_stale_format():
    """测试 #待压人 格式"""
    stale_data = [
        {
            "operation": "H11-1",
            "cn_name": "惊霆行动-1",
            "difficulty": "normal",
            "ageDays": 412,
            "records": [
                {
                    "team": [{"name": "司霆惊蛰"}, {"name": "黑角"}],
                    "url": "https://www.bilibili.com/video/BV1xx411c7mD"
                }
            ]
        }
    ]
    
    result = format_stale("惊霆无声", "四星队", 365, stale_data)
    print("\n--- #待压人 格式 ---")
    print(result)
    
    checks = [
        ("标题", "⏰" in result and "待压人" in result),
        ("天数", "超过365天" in result),
        ("关卡名", "H11-1" in result and "惊霆行动-1" in result),
        ("天数显示", "412天前" in result),
        ("人数显示", "2人" in result),
        ("BV号", "BV1xx411c7mD" in result),
    ]
    
    for check_name, passed in checks:
        if passed:
            log_test("FMT-030", f"待压人-{check_name}", "PASS")
        else:
            log_test("FMT-030", f"待压人-{check_name}", "FAIL",
                    result[:100], f"包含{check_name}")

    # FMT-031: 空结果
    result = format_stale("惊霆无声", "四星队", 365, [])
    if "无待压人记录" in result:
        log_test("FMT-031", "待压人-空结果", "PASS")
    else:
        log_test("FMT-031", "待压人-空结果", "FAIL",
                result[:100], "包含'无待压人记录'")

    # FMT-032: 突袭难度标签
    stale_challenge = [
        {
            "operation": "H11-1",
            "cn_name": "惊霆行动-1",
            "difficulty": "challenge",
            "ageDays": 300,
            "records": [{"team": [{"name": "司霆惊蛰"}, {"name": "黑角"}], "url": ""}]
        }
    ]
    result = format_stale("惊霆无声", "四星队", 365, stale_challenge)
    if "[突袭]" in result:
        log_test("FMT-032", "待压人-突袭标签", "PASS")
    else:
        log_test("FMT-032", "待压人-突袭标签", "FAIL",
                result[:100], "包含'[突袭]'")

def test_uncleared_format():
    """测试 #未通关 格式"""
    uncleared_data = [
        {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge", "hasChallenge": True},
        {"operation": "H11-3", "cn_name": "惊霆行动-3", "difficulty": "normal", "hasChallenge": False}
    ]
    
    operation_index = {
        "by_operation": {
            "H11-1": {"has_challenge": True},
            "H11-3": {"has_challenge": False}
        }
    }
    
    result = format_uncleared("惊霆无声", "四星队", uncleared_data, operation_index)
    print("\n--- #未通关 格式 ---")
    print(result)
    
    checks = [
        ("标题", "📌" in result and "未通关关卡" in result),
        ("数量", "2个" in result),
        ("关卡名", "H11-1" in result and "H11-3" in result),
        ("难度标签", "[突袭]" in result),  # H11-3没有突袭模式，不显示[普通]标签
    ]
    
    for check_name, passed in checks:
        if passed:
            log_test("FMT-020", f"未通关-{check_name}", "PASS")
        else:
            log_test("FMT-020", f"未通关-{check_name}", "FAIL",
                    result[:100], f"包含{check_name}")

    # FMT-021: 空结果
    result = format_uncleared("惊霆无声", "四星队", [], operation_index)
    if "所有关卡已通关" in result:
        log_test("FMT-021", "未通关-空结果", "PASS")
    else:
        log_test("FMT-021", "未通关-空结果", "FAIL",
                result[:100], "包含'所有关卡已通关'")

def main():
    """执行所有格式化测试"""
    test_record_format()
    test_help_format()
    test_category_format()
    test_stale_format()
    test_uncleared_format()
    
    # 生成总结
    print("\n" + "=" * 60)
    print("展示格式测试总结")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"总用例数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
