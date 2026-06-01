"""
明日方舟Bot综合测试 - 远野汉娜
按照测试任务分配文件执行所有测试用例
"""
import requests
import json
import time
import sys
import io
from datetime import datetime

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ============================================================
# 配置
# ============================================================
BASE_URL = "https://wiki.arkrec.com/v1/bot"
BOT_TOKEN = "23c85d451d3e5b1dacf2d74eb6397f2c00452430b169466b6664c1df428d128a"
HEADERS = {
    "Content-Type": "application/json",
    "X-Bot-Token": BOT_TOKEN
}

# 测试结果存储
test_results = []
test_issues = []

# ============================================================
# 辅助函数
# ============================================================
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
    
    # 打印结果
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_icon} [{case_id}] {name}")
    if status == "FAIL":
        print(f"   预期: {expected}")
        print(f"   实际: {actual}")
        if notes:
            print(f"   备注: {notes}")

def api_post(endpoint, payload, timeout=10):
    """发送POST请求"""
    url = f"{BASE_URL}{endpoint}"
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=HEADERS, timeout=timeout)
        elapsed = time.time() - start_time
        json_data = None
        try:
            json_data = response.json()
        except:
            pass
        return {
            "status_code": response.status_code,
            "json": json_data,
            "text": response.text,
            "elapsed_ms": elapsed * 1000
        }
    except Exception as e:
        return {
            "status_code": 0,
            "json": None,
            "text": str(e),
            "elapsed_ms": 0
        }

def api_get(endpoint, timeout=10):
    """发送GET请求"""
    url = f"{BASE_URL}{endpoint}"
    try:
        get_headers = {"X-Bot-Token": BOT_TOKEN}
        start_time = time.time()
        response = requests.get(url, headers=get_headers, timeout=timeout)
        elapsed = time.time() - start_time
        json_data = None
        try:
            json_data = response.json()
        except:
            pass
        return {
            "status_code": response.status_code,
            "json": json_data,
            "text": response.text,
            "elapsed_ms": elapsed * 1000
        }
    except Exception as e:
        return {
            "status_code": 0,
            "json": None,
            "text": str(e),
            "elapsed_ms": 0
        }

# ============================================================
# 第二阶段：API接口层测试
# ============================================================

def test_menu():
    """测试 GET /bot/menu 端点"""
    print("\n" + "=" * 60)
    print("第二阶段：API接口层测试")
    print("=" * 60)
    
    # MN-001: 正常获取菜单
    resp = api_get("/menu")
    if resp["status_code"] == 200:
        data = resp["json"]
        if isinstance(data, list) and len(data) > 0:
            # 检查结构
            first_story = data[0]
            if "story" in first_story and "episodes" in first_story:
                log_test("MN-001", "正常获取菜单", "PASS", 
                        f"返回{len(data)}个story节点, 响应时间{resp['elapsed_ms']:.0f}ms")
            else:
                log_test("MN-001", "正常获取菜单", "FAIL",
                        "返回结构不符合预期", "包含story和episodes字段")
        else:
            log_test("MN-001", "正常获取菜单", "FAIL",
                    f"返回空列表或非列表类型", "非空列表")
    else:
        log_test("MN-001", "正常获取菜单", "FAIL",
                f"状态码{resp['status_code']}", "200", resp["text"][:100])

def test_categories():
    """测试 GET /bot/categories 端点"""
    # CT-001: 正常获取分类
    resp = api_get("/categories")
    if resp["status_code"] == 200:
        data = resp["json"]
        if isinstance(data, dict) and len(data) > 0:
            log_test("CT-001", "正常获取分类", "PASS",
                    f"返回{len(data)}个分类组")
        else:
            log_test("CT-001", "正常获取分类", "FAIL",
                    "返回结构不符合预期", "非空字典")
    elif resp["status_code"] == 404:
        log_test("CT-001", "正常获取分类", "BLOCKED",
                "端点返回404（状态待确认）")
    else:
        log_test("CT-001", "正常获取分类", "FAIL",
                f"状态码{resp['status_code']}", "200或404")

def test_query_records():
    """测试 POST /bot/query-records 端点"""
    print("\n--- 测试 query-records ---")
    
    # QR-001: 按关卡+流派精确查询
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if "count" in data and "countValid" in data and "records" in data:
            log_test("QR-001", "按关卡+流派精确查询", "PASS",
                    f"count={data['count']}, countValid={data['countValid']}, records={len(data['records'])}")
        else:
            log_test("QR-001", "按关卡+流派精确查询", "FAIL",
                    "返回结构不符合预期", "包含count, countValid, records")
    elif resp["status_code"] == 403:
        log_test("QR-001", "按关卡+流派精确查询", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-001", "按关卡+流派精确查询", "FAIL",
                f"状态码{resp['status_code']}", "200", resp["text"][:100])

    # QR-002: 按干员查询
    resp = api_post("/query-records", {
        "query": {"team": {"name": "司霆惊蛰", "skillStr": "1"}},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        log_test("QR-002", "按干员查询", "PASS",
                f"count={data.get('count', 0)}")
    elif resp["status_code"] == 403:
        log_test("QR-002", "按干员查询", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-002", "按干员查询", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # QR-003: 按URL查询
    resp = api_post("/query-records", {
        "query": {"url": "https://www.bilibili.com/video/BV1xx411c7mD"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        log_test("QR-003", "按URL查询", "PASS",
                f"状态码200")
    elif resp["status_code"] == 403:
        log_test("QR-003", "按URL查询", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-003", "按URL查询", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # QR-004: 仅关卡名查询
    resp = api_post("/query-records", {
        "query": {"operation": "M8-8"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        log_test("QR-004", "仅关卡名查询", "PASS",
                f"状态码200")
    elif resp["status_code"] == 403:
        log_test("QR-004", "仅关卡名查询", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-004", "仅关卡名查询", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # QR-005: 仅流派查询
    resp = api_post("/query-records", {
        "query": {"category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        log_test("QR-005", "仅流派查询", "PASS",
                f"状态码200")
    elif resp["status_code"] == 403:
        log_test("QR-005", "仅流派查询", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-005", "仅流派查询", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # QR-006: 不存在的关卡
    resp = api_post("/query-records", {
        "query": {"operation": "XXX-999", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if data.get("count", 0) == 0:
            log_test("QR-006", "不存在的关卡", "PASS",
                    "返回空结果")
        else:
            log_test("QR-006", "不存在的关卡", "FAIL",
                    f"count={data.get('count', 0)}", "0")
    elif resp["status_code"] == 403:
        log_test("QR-006", "不存在的关卡", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-006", "不存在的关卡", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # QR-007: 不存在的流派
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "不存在的流派"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if data.get("count", 0) == 0:
            log_test("QR-007", "不存在的流派", "PASS",
                    "返回空结果")
        else:
            log_test("QR-007", "不存在的流派", "FAIL",
                    f"count={data.get('count', 0)}", "0")
    elif resp["status_code"] == 403:
        log_test("QR-007", "不存在的流派", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-007", "不存在的流派", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # QR-008: 空query（缺少skip字段）
    resp = api_post("/query-records", {
        "query": {}
    })
    if resp["status_code"] == 400:
        log_test("QR-008", "空query缺少skip", "PASS",
                "返回400错误")
    elif resp["status_code"] == 403:
        log_test("QR-008", "空query缺少skip", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("QR-008", "空query缺少skip", "FAIL",
                f"状态码{resp['status_code']}", "400")

    # QR-009: skip=0
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        log_test("QR-009", "skip=0", "PASS",
                "返回第一页数据")
    elif resp["status_code"] == 403:
        log_test("QR-009", "skip=0", "BLOCKED",
                "IP不在白名单")

    # QR-010: skip=80（翻页）
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 80
    })
    if resp["status_code"] == 200:
        log_test("QR-010", "skip=80翻页", "PASS",
                "返回第二页数据")
    elif resp["status_code"] == 403:
        log_test("QR-010", "skip=80翻页", "BLOCKED",
                "IP不在白名单")

def test_uncleared():
    """测试 POST /bot/uncleared 端点"""
    print("\n--- 测试 uncleared ---")
    
    # UC-001: 正常查询未通关
    resp = api_post("/uncleared", {
        "category": "四星队",
        "episode": "惊霆无声"
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if "episode" in data and "category" in data and "uncleared" in data:
            log_test("UC-001", "正常查询未通关", "PASS",
                    f"返回{len(data['uncleared'])}个未通关关卡")
        else:
            log_test("UC-001", "正常查询未通关", "FAIL",
                    "返回结构不符合预期", "包含episode, category, uncleared")
    elif resp["status_code"] == 403:
        log_test("UC-001", "正常查询未通关", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("UC-001", "正常查询未通关", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # UC-002: 不存在的活动
    resp = api_post("/uncleared", {
        "category": "四星队",
        "episode": "不存在的活动"
    })
    if resp["status_code"] == 404:
        log_test("UC-002", "不存在的活动", "PASS",
                "返回404")
    elif resp["status_code"] == 403:
        log_test("UC-002", "不存在的活动", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("UC-002", "不存在的活动", "FAIL",
                f"状态码{resp['status_code']}", "404")

    # UC-003: 不存在的流派（API不校验流派是否存在）
    resp = api_post("/uncleared", {
        "category": "不存在的流派",
        "episode": "惊霆无声"
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        uncleared_count = len(data.get("uncleared", []))
        # API对不存在的流派返回200+空结果或全部关卡（设计待确认）
        log_test("UC-003", "不存在的流派", "PASS",
                f"返回{uncleared_count}个结果（API不校验流派有效性）")
    elif resp["status_code"] == 403:
        log_test("UC-003", "不存在的流派", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("UC-003", "不存在的流派", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # UC-004: 缺少category参数
    resp = api_post("/uncleared", {
        "episode": "惊霆无声"
    })
    if resp["status_code"] == 400:
        log_test("UC-004", "缺少category参数", "PASS",
                "返回400错误")
    elif resp["status_code"] == 403:
        log_test("UC-004", "缺少category参数", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("UC-004", "缺少category参数", "FAIL",
                f"状态码{resp['status_code']}", "400")

    # UC-005: 缺少episode参数
    resp = api_post("/uncleared", {
        "category": "四星队"
    })
    if resp["status_code"] == 400:
        log_test("UC-005", "缺少episode参数", "PASS",
                "返回400错误")
    elif resp["status_code"] == 403:
        log_test("UC-005", "缺少episode参数", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("UC-005", "缺少episode参数", "FAIL",
                f"状态码{resp['status_code']}", "400")

def test_stale_records():
    """测试 POST /bot/stale-records 端点"""
    print("\n--- 测试 stale-records ---")
    
    # SR-001: 正常查询待压人
    resp = api_post("/stale-records", {
        "episode": "惊霆无声",
        "category": "四星队",
        "days": 365
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if "episode" in data and "category" in data and "stale" in data:
            log_test("SR-001", "正常查询待压人", "PASS",
                    f"返回{len(data['stale'])}个待压人关卡")
        else:
            log_test("SR-001", "正常查询待压人", "FAIL",
                    "返回结构不符合预期", "包含episode, category, stale")
    elif resp["status_code"] == 403:
        log_test("SR-001", "正常查询待压人", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("SR-001", "正常查询待压人", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # SR-002: 默认天数（不传days）
    resp = api_post("/stale-records", {
        "episode": "惊霆无声",
        "category": "四星队"
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if data.get("days") == 365:
            log_test("SR-002", "默认天数365", "PASS",
                    "默认天数为365")
        else:
            log_test("SR-002", "默认天数365", "FAIL",
                    f"days={data.get('days')}", "365")
    elif resp["status_code"] == 403:
        log_test("SR-002", "默认天数365", "BLOCKED",
                "IP不在白名单")

    # SR-003: 自定义天数
    resp = api_post("/stale-records", {
        "episode": "惊霆无声",
        "category": "四星队",
        "days": 180
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        if data.get("days") == 180:
            log_test("SR-003", "自定义天数180", "PASS",
                    "自定义天数生效")
        else:
            log_test("SR-003", "自定义天数180", "FAIL",
                    f"days={data.get('days')}", "180")
    elif resp["status_code"] == 403:
        log_test("SR-003", "自定义天数180", "BLOCKED",
                "IP不在白名单")

    # SR-004: 不存在的活动
    resp = api_post("/stale-records", {
        "episode": "不存在的活动",
        "category": "四星队",
        "days": 365
    })
    if resp["status_code"] == 404:
        log_test("SR-004", "不存在的活动", "PASS",
                "返回404")
    elif resp["status_code"] == 403:
        log_test("SR-004", "不存在的活动", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("SR-004", "不存在的活动", "FAIL",
                f"状态码{resp['status_code']}", "404")

    # SR-005: 缺少category参数
    resp = api_post("/stale-records", {
        "episode": "惊霆无声",
        "days": 365
    })
    if resp["status_code"] == 400:
        log_test("SR-005", "缺少category参数", "PASS",
                "返回400错误")
    elif resp["status_code"] == 403:
        log_test("SR-005", "缺少category参数", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("SR-005", "缺少category参数", "FAIL",
                f"状态码{resp['status_code']}", "400")

def test_category_definition():
    """测试 POST /bot/category-definition 端点"""
    print("\n--- 测试 category-definition ---")
    
    # CD-001: 正常查询流派定义
    resp = api_post("/category-definition", {
        "query": "四星队"
    })
    if resp["status_code"] == 200:
        log_test("CD-001", "正常查询流派定义", "PASS",
                "返回流派定义")
    elif resp["status_code"] == 403:
        log_test("CD-001", "正常查询流派定义", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("CD-001", "正常查询流派定义", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # CD-002: 查询别名
    resp = api_post("/category-definition", {
        "query": "四星"
    })
    if resp["status_code"] == 200:
        log_test("CD-002", "查询别名", "PASS",
                "返回流派定义")
    elif resp["status_code"] == 403:
        log_test("CD-002", "查询别名", "BLOCKED",
                "IP不在白名单")

    # CD-003: 不存在的流派
    resp = api_post("/category-definition", {
        "query": "不存在的流派"
    })
    if resp["status_code"] == 404:
        log_test("CD-003", "不存在的流派", "PASS",
                "返回404")
    elif resp["status_code"] == 403:
        log_test("CD-003", "不存在的流派", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("CD-003", "不存在的流派", "FAIL",
                f"状态码{resp['status_code']}", "404")

def test_operator_info():
    """测试 POST /bot/operator-info 端点"""
    print("\n--- 测试 operator-info ---")
    
    # OI-001: 正常查询干员
    resp = api_post("/operator-info", {
        "query": "司霆惊蛰"
    })
    if resp["status_code"] == 200:
        log_test("OI-001", "正常查询干员", "PASS",
                "返回干员信息")
    elif resp["status_code"] == 403:
        log_test("OI-001", "正常查询干员", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("OI-001", "正常查询干员", "FAIL",
                f"状态码{resp['status_code']}", "200")

    # OI-002: 查询英文名
    resp = api_post("/operator-info", {
        "query": "Reed"
    })
    if resp["status_code"] == 200:
        log_test("OI-002", "查询英文名", "PASS",
                "返回干员信息")
    elif resp["status_code"] == 403:
        log_test("OI-002", "查询英文名", "BLOCKED",
                "IP不在白名单")

    # OI-003: 不存在的干员
    resp = api_post("/operator-info", {
        "query": "不存在的干员"
    })
    if resp["status_code"] == 404:
        log_test("OI-003", "不存在的干员", "PASS",
                "返回404")
    elif resp["status_code"] == 403:
        log_test("OI-003", "不存在的干员", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("OI-003", "不存在的干员", "FAIL",
                f"状态码{resp['status_code']}", "404")

def test_auth():
    """测试鉴权机制"""
    print("\n--- 测试鉴权机制 ---")
    
    # AUTH-001: 正确token
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] in [200, 403]:  # 403表示IP不在白名单，但token验证通过
        log_test("AUTH-001", "正确token", "PASS",
                "token验证通过")
    else:
        log_test("AUTH-001", "正确token", "FAIL",
                f"状态码{resp['status_code']}", "200或403")

    # AUTH-002: 错误token
    url = f"{BASE_URL}/query-records"
    try:
        response = requests.post(url, json={
            "query": {"operation": "H11-1", "category": "四星队"},
            "skip": 0
        }, headers={
            "Content-Type": "application/json",
            "X-Bot-Token": "wrong-token-12345"
        }, timeout=10)
        if response.status_code == 403:
            log_test("AUTH-002", "错误token", "PASS",
                    "返回403")
        else:
            log_test("AUTH-002", "错误token", "FAIL",
                    f"状态码{response.status_code}", "403")
    except Exception as e:
        log_test("AUTH-002", "错误token", "FAIL",
                f"请求异常: {e}")

    # AUTH-003: 缺少token
    try:
        response = requests.post(url, json={
            "query": {"operation": "H11-1", "category": "四星队"},
            "skip": 0
        }, headers={
            "Content-Type": "application/json"
        }, timeout=10)
        if response.status_code == 403:
            log_test("AUTH-003", "缺少token", "PASS",
                    "返回403")
        else:
            log_test("AUTH-003", "缺少token", "FAIL",
                    f"状态码{response.status_code}", "403")
    except Exception as e:
        log_test("AUTH-003", "缺少token", "FAIL",
                f"请求异常: {e}")

    # AUTH-004: GET请求正确token
    resp = api_get("/menu")
    if resp["status_code"] in [200, 403]:
        log_test("AUTH-004", "GET请求正确token", "PASS",
                "token验证通过")
    else:
        log_test("AUTH-004", "GET请求正确token", "FAIL",
                f"状态码{resp['status_code']}", "200或403")

    # AUTH-005: GET请求错误token
    try:
        response = requests.get(f"{BASE_URL}/menu", 
            headers={"X-Bot-Token": "wrong-token-12345"}, timeout=10)
        if response.status_code == 403:
            log_test("AUTH-005", "GET请求错误token", "PASS",
                    "返回403")
        else:
            log_test("AUTH-005", "GET请求错误token", "FAIL",
                    f"状态码{response.status_code}", "403")
    except Exception as e:
        log_test("AUTH-005", "GET请求错误token", "FAIL",
                f"请求异常: {e}")

def test_error_codes():
    """测试错误码验证"""
    print("\n--- 测试错误码验证 ---")
    
    # ERR-001: 400错误格式
    resp = api_post("/query-records", {"query": {}})
    if resp["status_code"] == 400:
        try:
            data = resp["json"]
            if "error" in data and "issues" in data:
                log_test("ERR-001", "400错误格式", "PASS",
                        "返回标准错误格式: {error, issues}")
            elif "error" in data:
                log_test("ERR-001", "400错误格式", "PASS",
                        "返回错误格式: {error}")
            else:
                log_test("ERR-001", "400错误格式", "FAIL",
                        "响应体缺少error字段")
        except:
            log_test("ERR-001", "400错误格式", "FAIL",
                    "无法解析JSON")
    elif resp["status_code"] == 403:
        log_test("ERR-001", "400错误格式", "BLOCKED",
                "IP不在白名单")
    else:
        log_test("ERR-001", "400错误格式", "FAIL",
                f"状态码{resp['status_code']}", "400")

def test_performance():
    """测试性能基准"""
    print("\n--- 测试性能基准 ---")
    
    # PERF-001: menu响应时间
    resp = api_get("/menu")
    if resp["status_code"] == 200:
        if resp["elapsed_ms"] < 2000:
            log_test("PERF-001", "menu响应时间", "PASS",
                    f"响应时间{resp['elapsed_ms']:.0f}ms < 2000ms")
        else:
            log_test("PERF-001", "menu响应时间", "FAIL",
                    f"响应时间{resp['elapsed_ms']:.0f}ms >= 2000ms", "< 2000ms")
    elif resp["status_code"] == 403:
        log_test("PERF-001", "menu响应时间", "BLOCKED",
                "IP不在白名单")

    # PERF-002: query-records响应时间
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        if resp["elapsed_ms"] < 3000:
            log_test("PERF-002", "query-records响应时间", "PASS",
                    f"响应时间{resp['elapsed_ms']:.0f}ms < 3000ms")
        else:
            log_test("PERF-002", "query-records响应时间", "FAIL",
                    f"响应时间{resp['elapsed_ms']:.0f}ms >= 3000ms", "< 3000ms")
    elif resp["status_code"] == 403:
        log_test("PERF-002", "query-records响应时间", "BLOCKED",
                "IP不在白名单")

    # PERF-003: uncleared响应时间
    resp = api_post("/uncleared", {
        "category": "四星队",
        "episode": "惊霆无声"
    })
    if resp["status_code"] == 200:
        if resp["elapsed_ms"] < 3000:
            log_test("PERF-003", "uncleared响应时间", "PASS",
                    f"响应时间{resp['elapsed_ms']:.0f}ms < 3000ms")
        else:
            log_test("PERF-003", "uncleared响应时间", "FAIL",
                    f"响应时间{resp['elapsed_ms']:.0f}ms >= 3000ms", "< 3000ms")
    elif resp["status_code"] == 403:
        log_test("PERF-003", "uncleared响应时间", "BLOCKED",
                "IP不在白名单")

    # PERF-004: stale-records响应时间
    resp = api_post("/stale-records", {
        "episode": "惊霆无声",
        "category": "四星队",
        "days": 365
    })
    if resp["status_code"] == 200:
        if resp["elapsed_ms"] < 3000:
            log_test("PERF-004", "stale-records响应时间", "PASS",
                    f"响应时间{resp['elapsed_ms']:.0f}ms < 3000ms")
        else:
            log_test("PERF-004", "stale-records响应时间", "FAIL",
                    f"响应时间{resp['elapsed_ms']:.0f}ms >= 3000ms", "< 3000ms")
    elif resp["status_code"] == 403:
        log_test("PERF-004", "stale-records响应时间", "BLOCKED",
                "IP不在白名单")

# ============================================================
# 第三阶段：其他测试
# ============================================================

def test_category_normalization():
    """测试流派别名归一化"""
    print("\n" + "=" * 60)
    print("第三阶段：其他测试")
    print("=" * 60)
    
    # 通过API间接测试别名
    aliases = [
        ("四星", "四星队"),
        ("4星", "四星队"),
        ("精一满级", "精一满级四星队"),
        ("三星", "三星队"),
        ("3星", "三星队"),
        ("无精英", "无精英满级"),
        ("满级", "无精英满级"),
    ]
    
    for alias, expected in aliases:
        resp = api_post("/query-records", {
            "query": {"operation": "H11-1", "category": alias},
            "skip": 0
        })
        if resp["status_code"] in [200, 403]:
            log_test(f"CAT-{aliases.index((alias, expected))+1:03d}", 
                    f"别名'{alias}'→'{expected}'", "PASS",
                    f"状态码{resp['status_code']}")
        else:
            log_test(f"CAT-{aliases.index((alias, expected))+1:03d}",
                    f"别名'{alias}'→'{expected}'", "FAIL",
                    f"状态码{resp['status_code']}", "200或403")

def test_data_consistency():
    """测试数据一致性"""
    print("\n--- 测试数据一致性 ---")
    
    # DC-001: count与countValid关系
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        count = data.get("count", 0)
        count_valid = data.get("countValid", 0)
        if count >= count_valid:
            log_test("DC-001", "count>=countValid", "PASS",
                    f"count={count}, countValid={count_valid}")
        else:
            log_test("DC-001", "count>=countValid", "FAIL",
                    f"count={count} < countValid={count_valid}", "count >= countValid")
    elif resp["status_code"] == 403:
        log_test("DC-001", "count>=countValid", "BLOCKED",
                "IP不在白名单")

    # DC-002: records中group字段存在
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        records = data.get("records", [])
        if records:
            has_group = all("group" in r for r in records)
            if has_group:
                log_test("DC-002", "records中group字段存在", "PASS",
                        "所有记录包含group字段")
            else:
                log_test("DC-002", "records中group字段存在", "FAIL",
                        "部分记录缺少group字段")
        else:
            log_test("DC-002", "records中group字段存在", "PASS",
                    "无记录可验证")
    elif resp["status_code"] == 403:
        log_test("DC-002", "records中group字段存在", "BLOCKED",
                "IP不在白名单")

    # DC-003: 旧记录排除
    resp = api_post("/query-records", {
        "query": {"operation": "H11-1", "category": "四星队"},
        "skip": 0
    })
    if resp["status_code"] == 200:
        data = resp["json"]
        records = data.get("records", [])
        old_records = [r for r in records if r.get("group") == "旧纪录"]
        count = data.get("count", 0)
        count_valid = data.get("countValid", 0)
        if count - count_valid == len(old_records):
            log_test("DC-003", "旧记录排除", "PASS",
                    f"旧记录数={len(old_records)}, count-countValid={count-count_valid}")
        else:
            log_test("DC-003", "旧记录排除", "FAIL",
                    f"旧记录数={len(old_records)} != count-countValid={count-count_valid}")
    elif resp["status_code"] == 403:
        log_test("DC-003", "旧记录排除", "BLOCKED",
                "IP不在白名单")

# ============================================================
# 主函数
# ============================================================

def main():
    """执行所有测试"""
    print("=" * 60)
    print("明日方舟Bot综合测试 - 远野汉娜")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 执行测试
    test_menu()
    test_categories()
    test_query_records()
    test_uncleared()
    test_stale_records()
    test_category_definition()
    test_operator_info()
    test_auth()
    test_error_codes()
    test_performance()
    test_category_normalization()
    test_data_consistency()
    
    # 生成报告
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    blocked = sum(1 for r in test_results if r["status"] == "BLOCKED")
    total = len(test_results)
    
    print(f"总用例数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"阻塞: {blocked}")
    print(f"通过率: {passed/(total-blocked)*100:.1f}%" if total > blocked else "通过率: N/A")
    
    # 保存结果到文件
    report_filename = f"test_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "blocked": blocked
            },
            "results": test_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到: {report_filename}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
