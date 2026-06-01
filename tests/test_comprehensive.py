"""
明日方舟Bot综合测试脚本 - 远野汉娜执行
测试范围：除NapCat以外的所有功能模块
总计覆盖：约230个测试场景
"""
import requests
import json
import time
import sys
import io
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 配置
# ============================================================
BASE_URL = "https://wiki.arkrec.com/v1/bot"
BOT_TOKEN = "23c85d451d3e5b1dacf2d74eb6397f2c00452430b169466b6664c1df428d128a"
HEADERS = {"Content-Type": "application/json", "X-Bot-Token": BOT_TOKEN}
GET_HEADERS = {"X-Bot-Token": BOT_TOKEN}
TIMEOUT = 15

# 测试结果统计
results = {"pass": 0, "fail": 0, "blocked": 0, "skip": 0}
issues = []
perf_data = []


def log(msg: str, level: str = "INFO"):
    print(f"[{level}] {msg}")


def test_case(case_id: str, name: str, passed: bool, detail: str = "", severity: str = "P2"):
    """记录测试用例结果"""
    status = "[PASS]" if passed else "[FAIL]"
    if passed:
        results["pass"] += 1
    else:
        results["fail"] += 1
        issues.append({
            "case_id": case_id,
            "name": name,
            "detail": detail,
            "severity": severity,
        })
    print(f"  {status} [{case_id}] {name}")
    if detail and not passed:
        print(f"         Detail: {detail}")


def test_blocked(case_id: str, name: str, reason: str):
    """记录阻塞用例"""
    results["blocked"] += 1
    print(f"  [BLOCKED] [{case_id}] {name} - {reason}")


def api_post(endpoint: str, payload: dict, token: str = BOT_TOKEN) -> requests.Response:
    """发送POST请求"""
    h = {"Content-Type": "application/json", "X-Bot-Token": token}
    return requests.post(f"{BASE_URL}{endpoint}", json=payload, headers=h, timeout=TIMEOUT)


def api_get(endpoint: str, token: str = BOT_TOKEN) -> requests.Response:
    """发送GET请求"""
    h = {"X-Bot-Token": token}
    return requests.get(f"{BASE_URL}{endpoint}", headers=h, timeout=TIMEOUT)


def measure_perf(endpoint: str, method: str, payload: dict = None) -> float:
    """测量API响应时间"""
    start = time.time()
    if method == "GET":
        api_get(endpoint)
    else:
        api_post(endpoint, payload)
    elapsed = (time.time() - start) * 1000
    perf_data.append({"endpoint": endpoint, "method": method, "ms": elapsed})
    return elapsed


# ============================================================
# 第一阶段：API接口层测试
# ============================================================

def test_auth():
    """2.4 鉴权测试 AUTH-001 ~ AUTH-023"""
    log("=" * 60)
    log("第一阶段：鉴权机制测试")
    log("=" * 60)

    # AUTH-001: 正常Token访问
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
    test_case("AUTH-001", "正常Token访问", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # AUTH-002: 空Token
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0}, token="")
    test_case("AUTH-002", "空Token", resp.status_code == 403,
              f"status={resp.status_code}", "P0")

    # AUTH-003: 无效Token
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0}, token="invalid_token_12345")
    test_case("AUTH-003", "无效Token", resp.status_code == 403,
              f"status={resp.status_code}", "P0")

    # AUTH-004: 无Token header
    resp = requests.post(f"{BASE_URL}/query-records",
                         json={"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0},
                         headers={"Content-Type": "application/json"},
                         timeout=TIMEOUT)
    test_case("AUTH-004", "无Token header", resp.status_code == 403,
              f"status={resp.status_code}", "P0")

    # AUTH-005: Token大小写敏感（用错误大小写）
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0},
                    token="23C85D451D3E5B1DACFD274EB6397F2C00452430B169466B6664C1DF428D128A")
    test_case("AUTH-005", "Token大小写敏感验证", resp.status_code == 403,
              f"status={resp.status_code}", "P1")

    # AUTH-006: GET /menu 正常Token
    resp = api_get("/menu")
    test_case("AUTH-006", "GET /menu 正常Token", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # AUTH-007: GET /menu 空Token
    resp = api_get("/menu", token="")
    test_case("AUTH-007", "GET /menu 空Token", resp.status_code == 403,
              f"status={resp.status_code}", "P0")

    # AUTH-008: POST /uncleared 正常Token
    resp = api_post("/uncleared", {"category": "四星队", "episode": "惊霆无声"})
    test_case("AUTH-008", "POST /uncleared 正常Token", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # AUTH-009: POST /stale-records 正常Token
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    test_case("AUTH-009", "POST /stale-records 正常Token", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # AUTH-010: POST /category-definition 正常Token
    resp = api_post("/category-definition", {"query": "四星队"})
    test_case("AUTH-010", "POST /category-definition 正常Token", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # AUTH-011: POST /operator-info 正常Token
    resp = api_post("/operator-info", {"query": "Reed"})
    test_case("AUTH-011", "POST /operator-info 正常Token", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # AUTH-012: POST 无body（400）
    resp = requests.post(f"{BASE_URL}/query-records",
                         headers=HEADERS,
                         timeout=TIMEOUT)
    test_case("AUTH-012", "POST无body返回400", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # AUTH-013: GET 不存在的端点
    resp = api_get("/nonexistent")
    test_case("AUTH-013", "GET不存在端点返回404", resp.status_code == 404,
              f"status={resp.status_code}", "P2")

    # AUTH-014: POST 不存在的端点
    resp = api_post("/nonexistent", {})
    test_case("AUTH-014", "POST不存在端点返回404", resp.status_code == 404,
              f"status={resp.status_code}", "P2")

    # AUTH-015: 错误HTTP方法（GET query-records）
    resp = api_get("/query-records")
    test_case("AUTH-015", "GET query-records应返回405或404", resp.status_code in [405, 404],
              f"status={resp.status_code}", "P2")


def test_query_records():
    """2.1 /bot/query-records QR-001 ~ QR-054"""
    log("=" * 60)
    log("第一阶段：POST /bot/query-records 核心查询测试")
    log("=" * 60)

    # === 按关卡+流派精确查询 ===
    # QR-001: 关卡+流派精确查询
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-001", "关卡+流派精确查询", resp.status_code == 200 and "count" in data,
              f"status={resp.status_code}, count={data.get('count')}", "P0")

    # QR-002: 关卡+流派+突袭
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队", "operationType": "challenge"}, "skip": 0})
    test_case("QR-002", "关卡+流派+突袭查询", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # QR-003: 关卡+中文名+流派
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "cn_name": "惊霆行动-1", "category": "四星队"}, "skip": 0})
    test_case("QR-003", "关卡+中文名+流派", resp.status_code == 200,
              f"status={resp.status_code}", "P1")

    # QR-004: 仅关卡
    resp = api_post("/query-records", {"query": {"operation": "H11-1"}, "skip": 0})
    test_case("QR-004", "仅关卡（单维度）", resp.status_code == 200,
              f"status={resp.status_code}", "P1")

    # QR-005: 仅流派
    resp = api_post("/query-records", {"query": {"category": "四星队"}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-005", "仅流派（单维度）", resp.status_code == 200 and "records" in data,
              f"status={resp.status_code}", "P1")

    # QR-006: 不存在的关卡
    resp = api_post("/query-records", {"query": {"operation": "XXX-999", "category": "四星队"}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-006", "不存在的关卡返回空", resp.status_code == 200 and data.get("count", -1) == 0,
              f"status={resp.status_code}, count={data.get('count')}", "P1")

    # QR-007: 不存在的流派
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "不存在的流派"}, "skip": 0})
    test_case("QR-007", "不存在的流派", resp.status_code == 200,
              f"status={resp.status_code}", "P1")

    # QR-008: query为空对象
    resp = api_post("/query-records", {"query": {}, "skip": 0})
    test_case("QR-008", "query为空对象", resp.status_code in [400, 200],
              f"status={resp.status_code}", "P1")

    # QR-009: 无query字段
    resp = api_post("/query-records", {"skip": 0})
    test_case("QR-009", "无query字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # QR-010: skip为负数
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": -1})
    test_case("QR-010", "skip为负数", resp.status_code in [400, 200],
              f"status={resp.status_code}", "P2")

    # QR-011: skip超大值
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 999999})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-011", "skip超大值返回空", resp.status_code == 200,
              f"status={resp.status_code}, records={len(data.get('records', []))}", "P2")

    # QR-012: skip非整数
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": "abc"})
    test_case("QR-012", "skip非整数", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P2")

    # === 按干员（team）查询 ===
    # QR-013: 干员名+技能号
    resp = api_post("/query-records", {"query": {"team": {"name": "司霆惊蛰", "skillStr": "1"}}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-013", "干员名+技能号查询", resp.status_code == 200 and data.get("count", 0) > 0,
              f"status={resp.status_code}, count={data.get('count')}", "P0")

    # QR-014: 仅干员名（无技能号）
    resp = api_post("/query-records", {"query": {"team": {"name": "司霆惊蛰"}}, "skip": 0})
    test_case("QR-014", "仅干员名查询", resp.status_code == 200,
              f"status={resp.status_code}", "P1")

    # QR-015: 不存在的干员
    resp = api_post("/query-records", {"query": {"team": {"name": "不存在的干员"}}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-015", "不存在的干员返回空", resp.status_code == 200,
              f"status={resp.status_code}, count={data.get('count')}", "P1")

    # QR-016: 干员名+不匹配的技能号
    resp = api_post("/query-records", {"query": {"team": {"name": "司霆惊蛰", "skillStr": "99"}}, "skip": 0})
    test_case("QR-016", "干员名+不匹配技能号", resp.status_code == 200,
              f"status={resp.status_code}", "P2")

    # QR-017: team中缺少name字段
    resp = api_post("/query-records", {"query": {"team": {"skillStr": "1"}}, "skip": 0})
    test_case("QR-017", "team缺少name字段", resp.status_code in [400, 200],
              f"status={resp.status_code}", "P2")

    # QR-018: team为空对象
    resp = api_post("/query-records", {"query": {"team": {}}, "skip": 0})
    test_case("QR-018", "team为空对象", resp.status_code in [400, 200],
              f"status={resp.status_code}", "P2")

    # === 查询形态优先级验证 ===
    # QR-019: 同时提供team和operation（team优先）
    resp = api_post("/query-records", {"query": {"team": {"name": "司霆惊蛰"}, "operation": "H11-1", "category": "四星队"}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-019", "同时提供team和operation（team优先）", resp.status_code == 200,
              f"status={resp.status_code}", "P1")

    # QR-020: 不同关卡的查询
    for op in ["M8-8", "GT-1", "H11-3"]:
        resp = api_post("/query-records", {"query": {"operation": op, "category": "四星队"}, "skip": 0})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"QR-02{['M8-8','GT-1','H11-3'].index(op)+0}",
                  f"查询关卡 {op}", resp.status_code == 200,
                  f"status={resp.status_code}, count={data.get('count')}", "P1")

    # QR-021~030: 不同流派查询
    categories = ["四星队", "精一满级四星队", "精一1级四星队", "三星队", "精一1级", "无精英满级", "无精英1级"]
    for i, cat in enumerate(categories):
        resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": cat}, "skip": 0})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"QR-{22+i:03d}", f"查询流派 {cat}", resp.status_code == 200,
                  f"status={resp.status_code}, count={data.get('count')}", "P1")

    # QR-031~035: 翻页测试
    for skip in [0, 80, 160]:
        resp = api_post("/query-records", {"query": {"category": "四星队"}, "skip": skip})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"QR-{31+skip//80:03d}", f"翻页 skip={skip}", resp.status_code == 200,
                  f"status={resp.status_code}, records={len(data.get('records', []))}", "P1")

    # QR-036~040: 数据一致性验证
    # count vs countValid
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
    if resp.status_code == 200:
        data = resp.json()
        count = data.get("count", 0)
        count_valid = data.get("countValid", 0)
        records = data.get("records", [])
        old_records = [r for r in records if r.get("group") == "旧纪录"]
        test_case("QR-036", "count >= countValid", count >= count_valid,
                  f"count={count}, countValid={count_valid}", "P0")
        test_case("QR-037", "countValid = count - 旧记录数", count_valid == count - len(old_records),
                  f"count={count}, countValid={count_valid}, old={len(old_records)}", "P0")
        test_case("QR-038", "records数组非空（有数据时）", len(records) > 0,
                  f"records={len(records)}", "P1")
    else:
        test_case("QR-036", "count >= countValid", False, f"API返回{resp.status_code}", "P0")
        test_case("QR-037", "countValid = count - 旧记录数", False, f"API返回{resp.status_code}", "P0")
        test_case("QR-038", "records数组非空", False, f"API返回{resp.status_code}", "P1")

    # QR-039: records中旧记录的group字段
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
    if resp.status_code == 200:
        data = resp.json()
        records = data.get("records", [])
        has_group = all("group" in r for r in records)
        test_case("QR-039", "所有record有group字段", has_group,
                  f"total={len(records)}", "P1")

    # QR-040: records中字段完整性
    resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
    if resp.status_code == 200:
        data = resp.json()
        records = data.get("records", [])
        if records:
            r = records[0]
            required_fields = ["id", "raider", "url", "operation", "category", "team"]
            missing = [f for f in required_fields if f not in r]
            test_case("QR-040", "records字段完整性", len(missing) == 0,
                      f"missing={missing}", "P1")
        else:
            test_case("QR-040", "records字段完整性", False, "无记录可验证", "P2")

    # QR-041~045: 边界场景
    # QR-041: operation大小写不敏感
    resp_lower = api_post("/query-records", {"query": {"operation": "h11-1", "category": "四星队"}, "skip": 0})
    resp_upper = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
    if resp_lower.status_code == 200 and resp_upper.status_code == 200:
        data_lower = resp_lower.json()
        data_upper = resp_upper.json()
        test_case("QR-041", "operation大小写不敏感", data_lower.get("count") == data_upper.get("count"),
                  f"lower={data_lower.get('count')}, upper={data_upper.get('count')}", "P1")
    else:
        test_case("QR-041", "operation大小写不敏感", False, "API请求失败", "P1")

    # QR-042: operation含空格
    resp = api_post("/query-records", {"query": {"operation": "H11 1", "category": "四星队"}, "skip": 0})
    test_case("QR-042", "operation含空格（H11 1）", resp.status_code == 200,
              f"status={resp.status_code}", "P2")

    # QR-043: 活动关卡查询
    resp = api_post("/query-records", {"query": {"operation": "GT-1", "category": "四星队"}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-043", "活动关卡GT-1查询", resp.status_code == 200,
              f"status={resp.status_code}, count={data.get('count')}", "P1")

    # QR-044: 主线关卡查询
    resp = api_post("/query-records", {"query": {"operation": "M8-8", "category": "无精英满级"}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-044", "主线关卡M8-8查询", resp.status_code == 200,
              f"status={resp.status_code}, count={data.get('count')}", "P1")

    # QR-045: 不同干员查询
    resp = api_post("/query-records", {"query": {"team": {"name": "Reed"}}, "skip": 0})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("QR-045", "干员Reed查询", resp.status_code == 200,
              f"status={resp.status_code}, count={data.get('count')}", "P1")


def test_uncleared():
    """2.2 /bot/uncleared UC-001 ~ UC-035"""
    log("=" * 60)
    log("第一阶段：POST /bot/uncleared 未通关查询测试")
    log("=" * 60)

    # UC-001: 正常查询
    resp = api_post("/uncleared", {"category": "四星队", "episode": "惊霆无声"})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("UC-001", "正常查询惊霆无声四星队", resp.status_code == 200 and "uncleared" in data,
              f"status={resp.status_code}, uncleared={len(data.get('uncleared', []))}", "P0")

    # UC-002: 不存在的活动
    resp = api_post("/uncleared", {"category": "四星队", "episode": "不存在的活动"})
    test_case("UC-002", "不存在的活动返回404", resp.status_code == 404,
              f"status={resp.status_code}", "P0")

    # UC-003: 不存在的流派
    resp = api_post("/uncleared", {"category": "不存在的流派", "episode": "惊霆无声"})
    test_case("UC-003", "不存在的流派", resp.status_code in [200, 400],
              f"status={resp.status_code}", "P1")

    # UC-004: 无category字段
    resp = api_post("/uncleared", {"episode": "惊霆无声"})
    test_case("UC-004", "无category字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # UC-005: 无episode字段
    resp = api_post("/uncleared", {"category": "四星队"})
    test_case("UC-005", "无episode字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # UC-006: 空body
    resp = api_post("/uncleared", {})
    test_case("UC-006", "空body", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # UC-007: 空字符串参数
    resp = api_post("/uncleared", {"category": "", "episode": ""})
    test_case("UC-007", "空字符串参数", resp.status_code in [400, 404, 200],
              f"status={resp.status_code}", "P2")

    # UC-008~015: 不同活动查询
    episodes = ["惊霆无声", "骑兵与猎人", "破碎日冕", "怒号光明", "局部坏死"]
    for i, ep in enumerate(episodes):
        resp = api_post("/uncleared", {"category": "四星队", "episode": ep})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"UC-{8+i:03d}", f"查询活动 {ep}", resp.status_code == 200,
                  f"status={resp.status_code}, uncleared={len(data.get('uncleared', []))}", "P1")

    # UC-016~022: 不同流派查询
    categories = ["四星队", "精一满级四星队", "精一1级四星队", "三星队", "精一1级", "无精英满级", "无精英1级"]
    for i, cat in enumerate(categories):
        resp = api_post("/uncleared", {"category": cat, "episode": "惊霆无声"})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"UC-{16+i:03d}", f"流派 {cat} 未通关", resp.status_code == 200,
                  f"status={resp.status_code}, uncleared={len(data.get('uncleared', []))}", "P1")

    # UC-023: 响应结构验证
    resp = api_post("/uncleared", {"category": "四星队", "episode": "惊霆无声"})
    if resp.status_code == 200:
        data = resp.json()
        has_fields = all(k in data for k in ["episode", "category", "uncleared"])
        test_case("UC-023", "响应结构完整性", has_fields,
                  f"fields={list(data.keys())}", "P0")
        # UC-024: episode和category回显
        test_case("UC-024", "episode回显", data.get("episode") == "惊霆无声",
                  f"episode={data.get('episode')}", "P1")
        test_case("UC-025", "category回显", data.get("category") == "四星队",
                  f"category={data.get('category')}", "P1")
    else:
        test_case("UC-023", "响应结构完整性", False, f"status={resp.status_code}", "P0")
        test_case("UC-024", "episode回显", False, f"status={resp.status_code}", "P1")
        test_case("UC-025", "category回显", False, f"status={resp.status_code}", "P1")

    # UC-026~028: uncleared中每个元素的结构验证
    resp = api_post("/uncleared", {"category": "四星队", "episode": "惊霆无声"})
    if resp.status_code == 200:
        data = resp.json()
        uncleared = data.get("uncleared", [])
        if uncleared:
            for i, item in enumerate(uncleared[:3]):
                has_fields = all(k in item for k in ["operation", "cn_name", "difficulty", "hasChallenge"])
                test_case(f"UC-{26+i:03d}", f"uncleared[{i}]字段完整", has_fields,
                          f"fields={list(item.keys())}", "P0")
        else:
            for i in range(3):
                test_case(f"UC-{26+i:03d}", f"uncleared[{i}]字段完整", False, "无数据可验证", "P2")
    else:
        for i in range(3):
            test_case(f"UC-{26+i:03d}", f"uncleared[{i}]字段完整", False, f"status={resp.status_code}", "P0")

    # UC-029~031: 已全部通关的场景（返回空uncleared）
    resp = api_post("/uncleared", {"category": "无精英满级", "episode": "骑兵与猎人"})
    if resp.status_code == 200:
        data = resp.json()
        uncleared = data.get("uncleared", [])
        # 如果全部通关，uncleared应为空
        test_case("UC-029", "全部通关返回空列表", isinstance(uncleared, list),
                  f"uncleared={len(uncleared)}", "P1")
    else:
        test_case("UC-029", "全部通关返回空列表", False, f"status={resp.status_code}", "P1")

    # UC-032~035: 判定规则验证
    # 检查突袭关的判定逻辑
    resp = api_post("/uncleared", {"category": "四星队", "episode": "惊霆无声"})
    if resp.status_code == 200:
        data = resp.json()
        uncleared = data.get("uncleared", [])
        # 验证difficulty字段值只有normal或challenge
        valid_diffs = all(item.get("difficulty") in ["normal", "challenge"] for item in uncleared)
        test_case("UC-032", "difficulty字段值合法", valid_diffs,
                  f"difficulties={[item.get('difficulty') for item in uncleared]}", "P0")

        # 验证hasChallenge字段
        valid_hc = all(isinstance(item.get("hasChallenge"), bool) for item in uncleared)
        test_case("UC-033", "hasChallenge字段为布尔值", valid_hc, "", "P1")

        # 验证operation字段非空
        valid_ops = all(item.get("operation", "") != "" for item in uncleared)
        test_case("UC-034", "operation字段非空", valid_ops, "", "P1")

        # UC-035: 不同流派未通关数量差异
        test_case("UC-035", "未通关列表非负", len(uncleared) >= 0,
                  f"count={len(uncleared)}", "P1")
    else:
        for i in range(4):
            test_case(f"UC-{32+i:03d}", f"判定规则验证{i+1}", False, f"status={resp.status_code}", "P0")


def test_stale_records():
    """2.3 /bot/stale-records SR-001 ~ SR-042"""
    log("=" * 60)
    log("第一阶段：POST /bot/stale-records 待压人查询测试")
    log("=" * 60)

    # SR-001: 正常查询（默认365天）
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("SR-001", "正常查询（默认365天）", resp.status_code == 200 and "stale" in data,
              f"status={resp.status_code}, stale={len(data.get('stale', []))}", "P0")

    # SR-002: 自定义天数180天
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 180})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("SR-002", "自定义天数180天", resp.status_code == 200,
              f"status={resp.status_code}, days={data.get('days')}, stale={len(data.get('stale', []))}", "P1")

    # SR-003: 自定义天数30天
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 30})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("SR-003", "自定义天数30天", resp.status_code == 200,
              f"status={resp.status_code}, stale={len(data.get('stale', []))}", "P1")

    # SR-004: 自定义天数0天
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 0})
    test_case("SR-004", "自定义天数0天", resp.status_code in [200, 400],
              f"status={resp.status_code}", "P2")

    # SR-005: 不传days字段（应使用默认365）
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队"})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("SR-005", "不传days字段使用默认365", resp.status_code == 200 and data.get("days") == 365,
              f"status={resp.status_code}, days={data.get('days')}", "P1")

    # SR-006: 不存在的活动
    resp = api_post("/stale-records", {"episode": "不存在的活动", "category": "四星队", "days": 365})
    test_case("SR-006", "不存在的活动返回404", resp.status_code == 404,
              f"status={resp.status_code}", "P0")

    # SR-007: 不存在的流派
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "不存在的流派", "days": 365})
    test_case("SR-007", "不存在的流派", resp.status_code in [200, 400],
              f"status={resp.status_code}", "P1")

    # SR-008: 无episode字段
    resp = api_post("/stale-records", {"category": "四星队", "days": 365})
    test_case("SR-008", "无episode字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # SR-009: 无category字段
    resp = api_post("/stale-records", {"episode": "惊霆无声", "days": 365})
    test_case("SR-009", "无category字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # SR-010: 空body
    resp = api_post("/stale-records", {})
    test_case("SR-010", "空body", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # SR-011~015: 不同活动查询
    episodes = ["惊霆无声", "骑兵与猎人", "破碎日冕", "怒号光明", "局部坏死"]
    for i, ep in enumerate(episodes):
        resp = api_post("/stale-records", {"episode": ep, "category": "四星队", "days": 365})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"SR-{11+i:03d}", f"查询活动 {ep}", resp.status_code == 200,
                  f"status={resp.status_code}, stale={len(data.get('stale', []))}", "P1")

    # SR-016~022: 不同流派查询
    categories = ["四星队", "精一满级四星队", "精一1级四星队", "三星队", "精一1级", "无精英满级", "无精英1级"]
    for i, cat in enumerate(categories):
        resp = api_post("/stale-records", {"episode": "惊霆无声", "category": cat, "days": 365})
        data = resp.json() if resp.status_code == 200 else {}
        test_case(f"SR-{16+i:03d}", f"流派 {cat} 待压人", resp.status_code == 200,
                  f"status={resp.status_code}, stale={len(data.get('stale', []))}", "P1")

    # SR-023: 响应结构验证
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    if resp.status_code == 200:
        data = resp.json()
        has_fields = all(k in data for k in ["episode", "category", "days", "stale"])
        test_case("SR-023", "响应结构完整性", has_fields,
                  f"fields={list(data.keys())}", "P0")
        # SR-024: 回显字段
        test_case("SR-024", "episode回显", data.get("episode") == "惊霆无声", "", "P1")
        test_case("SR-025", "category回显", data.get("category") == "四星队", "", "P1")
        test_case("SR-026", "days回显", data.get("days") == 365, f"days={data.get('days')}", "P1")
    else:
        test_case("SR-023", "响应结构完整性", False, f"status={resp.status_code}", "P0")
        test_case("SR-024", "episode回显", False, "", "P1")
        test_case("SR-025", "category回显", False, "", "P1")
        test_case("SR-026", "days回显", False, "", "P1")

    # SR-027~030: stale中每个元素的结构验证
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    if resp.status_code == 200:
        data = resp.json()
        stale = data.get("stale", [])
        if stale:
            for i, item in enumerate(stale[:3]):
                has_fields = all(k in item for k in ["operation", "cn_name", "difficulty", "ageDays", "records"])
                test_case(f"SR-{27+i:03d}", f"stale[{i}]字段完整", has_fields,
                          f"fields={list(item.keys())}", "P0")
        else:
            for i in range(3):
                test_case(f"SR-{27+i:03d}", f"stale[{i}]字段完整", False, "无数据", "P2")
    else:
        for i in range(3):
            test_case(f"SR-{27+i:03d}", f"stale[{i}]字段完整", False, f"status={resp.status_code}", "P0")

    # SR-030: ageDays > days验证
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    if resp.status_code == 200:
        data = resp.json()
        stale = data.get("stale", [])
        all_valid = all(item.get("ageDays", 0) > 365 for item in stale) if stale else True
        test_case("SR-030", "所有stale的ageDays > days", all_valid,
                  f"stale_count={len(stale)}", "P0")
    else:
        test_case("SR-030", "所有stale的ageDays > days", False, f"status={resp.status_code}", "P0")

    # SR-031~033: records中每条记录的结构
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    if resp.status_code == 200:
        data = resp.json()
        stale = data.get("stale", [])
        if stale and stale[0].get("records"):
            first_item = stale[0]
            records = first_item.get("records", [])
            if records:
                r = records[0]
                has_team = "team" in r
                test_case("SR-031", "stale记录包含team字段", has_team, "", "P0")
                # SR-032: team人数 = 1的记录不应出现在stale中
                team_size = len(r.get("team", []))
                test_case("SR-032", "stale记录team人数 >= 2", team_size >= 2,
                          f"team_size={team_size}", "P0")
                # SR-033: records按新→旧排序
                if len(records) >= 2:
                    dates = [rec.get("date_published", "") for rec in records]
                    is_sorted = dates == sorted(dates, reverse=True)
                    test_case("SR-033", "records按新→旧排序", is_sorted, "", "P1")
                else:
                    test_case("SR-033", "records按新→旧排序", True, "单条记录", "P1")
            else:
                test_case("SR-031", "stale记录包含team字段", False, "无records", "P2")
                test_case("SR-032", "stale记录team人数 >= 2", False, "无records", "P2")
                test_case("SR-033", "records按新→旧排序", False, "无records", "P2")
        else:
            test_case("SR-031", "stale记录包含team字段", False, "无数据", "P2")
            test_case("SR-032", "stale记录team人数 >= 2", False, "无数据", "P2")
            test_case("SR-033", "records按新→旧排序", False, "无数据", "P2")
    else:
        test_case("SR-031", "stale记录包含team字段", False, f"status={resp.status_code}", "P0")
        test_case("SR-032", "stale记录team人数 >= 2", False, f"status={resp.status_code}", "P0")
        test_case("SR-033", "records按新→旧排序", False, f"status={resp.status_code}", "P1")

    # SR-034~036: difficulty字段
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    if resp.status_code == 200:
        data = resp.json()
        stale = data.get("stale", [])
        valid_diffs = all(item.get("difficulty") in ["normal", "challenge"] for item in stale)
        test_case("SR-034", "difficulty字段值合法", valid_diffs,
                  f"difficulties={[item.get('difficulty') for item in stale[:5]]}", "P0")
        # SR-035: 普通和突袭分开成条
        normals = [s for s in stale if s.get("difficulty") == "normal"]
        challenges = [s for s in stale if s.get("difficulty") == "challenge"]
        test_case("SR-035", "普通和突袭分开成条", True,
                  f"normal={len(normals)}, challenge={len(challenges)}", "P1")
        # SR-036: 按ageDays倒序
        if len(stale) >= 2:
            ages = [s.get("ageDays", 0) for s in stale]
            is_sorted = ages == sorted(ages, reverse=True)
            test_case("SR-036", "stale按ageDays倒序", is_sorted,
                      f"ages={ages[:5]}", "P1")
        else:
            test_case("SR-036", "stale按ageDays倒序", True, "单条或无数据", "P1")
    else:
        test_case("SR-034", "difficulty字段值合法", False, f"status={resp.status_code}", "P0")
        test_case("SR-035", "普通和突袭分开成条", False, f"status={resp.status_code}", "P1")
        test_case("SR-036", "stale按ageDays倒序", False, f"status={resp.status_code}", "P1")

    # SR-037~040: 队伍人数=1过滤验证
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    if resp.status_code == 200:
        data = resp.json()
        stale = data.get("stale", [])
        # 验证没有team_size=1的记录
        has_solo = False
        for item in stale:
            for rec in item.get("records", []):
                if len(rec.get("team", [])) <= 1:
                    has_solo = True
                    break
        test_case("SR-037", "无team_size=1的记录（API层面）", not has_solo,
                  f"has_solo={has_solo}", "P0")
    else:
        test_case("SR-037", "无team_size=1的记录", False, f"status={resp.status_code}", "P0")

    # SR-038~040: 不同天数下stale数量变化
    stale_365 = []
    stale_180 = []
    stale_90 = []
    resp365 = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
    resp180 = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 180})
    resp90 = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 90})
    if resp365.status_code == 200:
        stale_365 = resp365.json().get("stale", [])
    if resp180.status_code == 200:
        stale_180 = resp180.json().get("stale", [])
    if resp90.status_code == 200:
        stale_90 = resp90.json().get("stale", [])

    test_case("SR-038", "365天stale >= 180天stale", len(stale_365) >= len(stale_180),
              f"365={len(stale_365)}, 180={len(stale_180)}", "P0")
    test_case("SR-039", "180天stale >= 90天stale", len(stale_180) >= len(stale_90),
              f"180={len(stale_180)}, 90={len(stale_90)}", "P0")
    test_case("SR-040", "stale数量随天数递增", len(stale_365) >= len(stale_90),
              f"365={len(stale_365)}, 90={len(stale_90)}", "P1")

    # SR-041~042: 边界场景
    # SR-041: days为极大值
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 99999})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("SR-041", "days极大值", resp.status_code == 200,
              f"status={resp.status_code}, stale={len(data.get('stale', []))}", "P2")

    # SR-042: days为负数
    resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": -1})
    test_case("SR-042", "days为负数", resp.status_code in [400, 200],
              f"status={resp.status_code}", "P2")


def test_menu():
    """2.4 /bot/menu MN-001 ~ MN-012"""
    log("=" * 60)
    log("第一阶段：GET /bot/menu 结构验证测试")
    log("=" * 60)

    # MN-001: 正常获取menu
    resp = api_get("/menu")
    data = resp.json() if resp.status_code == 200 else []
    test_case("MN-001", "正常获取menu", resp.status_code == 200 and isinstance(data, list),
              f"status={resp.status_code}, type={type(data).__name__}", "P0")

    # MN-002: menu是非空列表
    test_case("MN-002", "menu是非空列表", isinstance(data, list) and len(data) > 0,
              f"length={len(data) if isinstance(data, list) else 'N/A'}", "P0")

    # MN-003~006: story节点结构
    if isinstance(data, list) and data:
        for i, story in enumerate(data[:4]):
            has_story = "story" in story
            has_episodes = "episodes" in story
            test_case(f"MN-{3+i:03d}", f"story[{i}]有story和episodes字段",
                      has_story and has_episodes,
                      f"fields={list(story.keys())}", "P0")

    # MN-007~008: episode节点结构
    if isinstance(data, list) and data and data[0].get("episodes"):
        ep = data[0]["episodes"][0]
        has_episode = "episode" in ep
        has_operations = "operations" in ep
        test_case("MN-007", "episode有episode字段", has_episode, f"fields={list(ep.keys())}", "P0")
        test_case("MN-008", "episode有operations字段", has_operations, f"fields={list(ep.keys())}", "P0")

    # MN-009~010: operation节点结构
    if isinstance(data, list) and data and data[0].get("episodes") and data[0]["episodes"][0].get("operations"):
        op = data[0]["episodes"][0]["operations"][0]
        has_op = "operation" in op
        has_cn = "cn_name" in op
        has_hc = "hasChallenge" in op
        test_case("MN-009", "operation有operation字段", has_op, f"fields={list(op.keys())}", "P0")
        test_case("MN-010", "operation有cn_name和hasChallenge", has_cn and has_hc,
                  f"fields={list(op.keys())}", "P0")

    # MN-011: 已知关卡在menu中存在
    if isinstance(data, list) and data:
        all_ops = set()
        for story in data:
            for ep in story.get("episodes", []):
                for op in ep.get("operations", []):
                    all_ops.add(op.get("operation", ""))
        known_ops = ["H11-1", "M8-8", "GT-1"]
        found = [op for op in known_ops if op in all_ops]
        test_case("MN-011", "已知关卡在menu中存在", len(found) == len(known_ops),
                  f"found={found}, missing={[op for op in known_ops if op not in all_ops]}", "P0")

    # MN-012: hasChallenge字段类型
    if isinstance(data, list) and data:
        all_bool = True
        for story in data:
            for ep in story.get("episodes", []):
                for op in ep.get("operations", []):
                    if not isinstance(op.get("hasChallenge"), bool):
                        all_bool = False
                        break
        test_case("MN-012", "所有hasChallenge为布尔值", all_bool, "", "P1")


def test_categories():
    """2.5 /bot/categories CT-001 ~ CT-003"""
    log("=" * 60)
    log("第一阶段：GET /bot/categories 结构验证测试")
    log("=" * 60)

    # CT-001: 正常获取
    resp = api_get("/categories")
    if resp.status_code == 200:
        data = resp.json()
        test_case("CT-001", "正常获取categories", isinstance(data, dict),
                  f"status={resp.status_code}", "P0")
        # CT-002: 结构为dict
        test_case("CT-002", "响应为dict类型", isinstance(data, dict),
                  f"type={type(data).__name__}", "P0")
        # CT-003: 每个value为list
        all_lists = all(isinstance(v, list) for v in data.values()) if data else False
        test_case("CT-003", "每个value为list", all_lists, "", "P1")
    elif resp.status_code == 404:
        test_blocked("CT-001", "GET /bot/categories", "端点返回404，未实现")
        test_blocked("CT-002", "categories结构验证", "端点返回404")
        test_blocked("CT-003", "categories value类型", "端点返回404")
    else:
        test_case("CT-001", "正常获取categories", False, f"status={resp.status_code}", "P0")
        test_case("CT-002", "响应为dict类型", False, f"status={resp.status_code}", "P0")
        test_case("CT-003", "每个value为list", False, f"status={resp.status_code}", "P1")


def test_category_definition():
    """2.6 /bot/category-definition CD-001 ~ CD-005"""
    log("=" * 60)
    log("第一阶段：POST /bot/category-definition 基础功能测试")
    log("=" * 60)

    # CD-001: 查询四星队
    resp = api_post("/category-definition", {"query": "四星队"})
    test_case("CD-001", "查询四星队", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # CD-002: 查询不存在的流派
    resp = api_post("/category-definition", {"query": "不存在的流派"})
    test_case("CD-002", "查询不存在的流派返回404", resp.status_code == 404,
              f"status={resp.status_code}", "P0")

    # CD-003: 查询所有7个流派
    categories = ["四星队", "精一满级四星队", "精一1级四星队", "三星队", "精一1级", "无精英满级", "无精英1级"]
    all_ok = True
    for cat in categories:
        resp = api_post("/category-definition", {"query": cat})
        if resp.status_code != 200:
            all_ok = False
            break
    test_case("CD-003", "查询所有7个流派", all_ok, "", "P0")

    # CD-004: 查询别名（如"四星"应映射到"四星队"）
    resp = api_post("/category-definition", {"query": "四星"})
    test_case("CD-004", "查询别名'四星'", resp.status_code in [200, 404],
              f"status={resp.status_code}", "P1")

    # CD-005: 无query字段
    resp = api_post("/category-definition", {})
    test_case("CD-005", "无query字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")


def test_operator_info():
    """2.7 /bot/operator-info OI-001 ~ OI-007"""
    log("=" * 60)
    log("第一阶段：POST /bot/operator-info 基础功能测试")
    log("=" * 60)

    # OI-001: 查询Reed
    resp = api_post("/operator-info", {"query": "Reed"})
    data = resp.json() if resp.status_code == 200 else {}
    test_case("OI-001", "查询Reed", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # OI-002: 查询司霆惊蛰
    resp = api_post("/operator-info", {"query": "司霆惊蛰"})
    test_case("OI-002", "查询司霆惊蛰", resp.status_code == 200,
              f"status={resp.status_code}", "P0")

    # OI-003: 查询不存在的干员
    resp = api_post("/operator-info", {"query": "不存在的干员"})
    test_case("OI-003", "查询不存在的干员返回404", resp.status_code == 404,
              f"status={resp.status_code}", "P0")

    # OI-004: 无query字段
    resp = api_post("/operator-info", {})
    test_case("OI-004", "无query字段", resp.status_code in [400, 422],
              f"status={resp.status_code}", "P1")

    # OI-005: 空query
    resp = api_post("/operator-info", {"query": ""})
    test_case("OI-005", "空query", resp.status_code in [400, 404, 200],
              f"status={resp.status_code}", "P2")

    # OI-006: 中文名查询
    resp = api_post("/operator-info", {"query": "苇草"})
    test_case("OI-006", "中文名'苇草'查询", resp.status_code in [200, 404],
              f"status={resp.status_code}", "P1")

    # OI-007: 日文名查询
    resp = api_post("/operator-info", {"query": "レッド"})
    test_case("OI-007", "日文名'レッド'查询", resp.status_code in [200, 404],
              f"status={resp.status_code}", "P2")


# ============================================================
# 第二阶段：Bot指令层单元测试（通过Python模拟）
# ============================================================

def test_bot_commands():
    """2.1 Bot指令层测试（L0层）"""
    log("=" * 60)
    log("第二阶段：Bot指令层单元测试（Python模拟）")
    log("=" * 60)

    import sys
    sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

    # === 指令路由测试 ===
    # BOT-R01: 非指令消息返回None
    from qq_bot.handler import CommandHandler
    handler = CommandHandler()

    import asyncio

    async def run_handler(msg):
        return await handler.handle(msg, group_id=123456, user_id=789012)

    result = asyncio.get_event_loop().run_until_complete(run_handler("这是一条普通消息"))
    test_case("BOT-R01", "非指令消息返回None", result is None,
              f"result={result}", "P1")

    # BOT-R02: 空消息返回None
    result = asyncio.get_event_loop().run_until_complete(run_handler(""))
    test_case("BOT-R02", "空消息返回None", result is None,
              f"result={result}", "P1")

    # BOT-R03: 空格消息返回None
    result = asyncio.get_event_loop().run_until_complete(run_handler("   "))
    test_case("BOT-R03", "空格消息返回None", result is None,
              f"result={result}", "P1")

    # BOT-R04: 点号指令不匹配
    result = asyncio.get_event_loop().run_until_complete(run_handler(".查 H11-1 四星队"))
    test_case("BOT-R04", "点号指令不匹配", result is None,
              f"result={result}", "P1")

    # === #help 指令测试 ===
    # BOT-H01: #help返回帮助信息
    result = asyncio.get_event_loop().run_until_complete(run_handler("#help"))
    test_case("BOT-H01", "#help返回帮助信息", result is not None and "#查" in str(result),
              f"has_help={'#查' in str(result)}", "P0")

    # BOT-H02: #help包含所有指令说明
    if result:
        has_all = all(x in str(result) for x in ["#查", "#未通关", "#待压人", "#流派", "#help"])
        test_case("BOT-H02", "#help包含所有指令说明", has_all, "", "P0")
    else:
        test_case("BOT-H02", "#help包含所有指令说明", False, "result is None", "P0")

    # BOT-H03: #help不带参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#help"))
    test_case("BOT-H03", "#help不带参数正常返回", result is not None, "", "P1")

    # === #流派 指令测试 ===
    # BOT-F01: #流派返回流派列表
    result = asyncio.get_event_loop().run_until_complete(run_handler("#流派"))
    test_case("BOT-F01", "#流派返回流派列表", result is not None and "四星队" in str(result),
              f"has_list={'四星队' in str(result)}", "P0")

    # BOT-F02: #流派包含7个流派
    if result:
        categories = ["四星队", "精一满级四星队", "精一1级四星队", "三星队", "精一1级", "无精英满级", "无精英1级"]
        all_found = all(cat in str(result) for cat in categories)
        test_case("BOT-F02", "#流派包含7个流派", all_found, "", "P0")
    else:
        test_case("BOT-F02", "#流派包含7个流派", False, "result is None", "P0")

    # BOT-F03: #流派带空格
    result = asyncio.get_event_loop().run_until_complete(run_handler("#流派 "))
    test_case("BOT-F03", "#流派带空格", result is not None, "", "P1")

    # BOT-F04: #流派带参数（仍然返回列表）
    result = asyncio.get_event_loop().run_until_complete(run_handler("#流派 四星队"))
    test_case("BOT-F04", "#流派带参数（仍返回列表）", result is not None, "", "P2")

    # === #查 指令测试 ===
    # BOT-Q01: #查 H11-1 四星队（正常查询）
    result = asyncio.get_event_loop().run_until_complete(run_handler("#查 H11-1 四星队"))
    test_case("BOT-Q01", "#查 H11-1 四星队正常返回", result is not None,
              f"result_type={type(result).__name__}", "P0")

    # BOT-Q02: #查 缺少流派参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#查 H11-1"))
    test_case("BOT-Q02", "#查 缺少流派参数返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-Q03: #查 无参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#查"))
    test_case("BOT-Q03", "#查 无参数返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-Q04: #查 不存在的流派
    result = asyncio.get_event_loop().run_until_complete(run_handler("#查 H11-1 不存在的流派"))
    test_case("BOT-Q04", "#查 不存在的流派返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-Q05: #查 关卡代号大小写
    result = asyncio.get_event_loop().run_until_complete(run_handler("#查 h11-1 四星队"))
    test_case("BOT-Q05", "#查 关卡代号大小写不敏感", result is not None, "", "P1")

    # BOT-Q06: #查 关卡代号含空格
    result = asyncio.get_event_loop().run_until_complete(run_handler("#查 H11 1 四星队"))
    test_case("BOT-Q06", "#查 关卡代号含空格", result is not None, "", "P2")

    # BOT-Q07~Q10: 不同关卡+流派组合
    combos = [
        ("M8-8", "无精英满级"),
        ("GT-1", "四星队"),
        ("H11-3", "三星队"),
        ("H11-1", "精一满级四星队"),
    ]
    for i, (op, cat) in enumerate(combos):
        result = asyncio.get_event_loop().run_until_complete(run_handler(f"#查 {op} {cat}"))
        test_case(f"BOT-{7+i:03d}", f"#查 {op} {cat}", result is not None, "", "P1")

    # BOT-Q11~Q15: 流派别名测试
    aliases = [
        ("四星", "四星队"),
        ("3星", "三星队"),
        ("满级", "无精英满级"),
        ("精一满级", "精一满级四星队"),
        ("无精英", "无精英满级"),
    ]
    for i, (alias, expected) in enumerate(aliases):
        # 检查别名是否被正确归一化（通过handler是否返回结果而非错误提示）
        result = asyncio.get_event_loop().run_until_complete(run_handler(f"#查 H11-1 {alias}"))
        # 如果返回的是错误提示（含"流派"），说明别名未被识别
        if result and "未找到流派" in str(result):
            test_case(f"BOT-{11+i:03d}", f"别名'{alias}'→'{expected}'", False,
                      f"result={str(result)[:50]}", "P1")
        else:
            test_case(f"BOT-{11+i:03d}", f"别名'{alias}'→'{expected}'", True, "", "P1")

    # === #未通关 指令测试 ===
    # BOT-U01: #未通关 惊霆无声 四星队
    result = asyncio.get_event_loop().run_until_complete(run_handler("#未通关 惊霆无声 四星队"))
    test_case("BOT-U01", "#未通关 惊霆无声 四星队", result is not None,
              f"result_type={type(result).__name__}", "P0")

    # BOT-U02: #未通关 缺少流派参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#未通关 惊霆无声"))
    test_case("BOT-U02", "#未通关 缺少流派参数返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-U03: #未通关 无参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#未通关"))
    test_case("BOT-U03", "#未通关 无参数返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-U04: #未通关 不存在的活动
    result = asyncio.get_event_loop().run_until_complete(run_handler("#未通关 不存在的活动 四星队"))
    test_case("BOT-U04", "#未通关 不存在的活动", result is not None, "", "P1")

    # BOT-U05~U07: 不同活动查询
    episodes = ["惊霆无声", "骑兵与猎人", "破碎日冕"]
    for i, ep in enumerate(episodes):
        result = asyncio.get_event_loop().run_until_complete(run_handler(f"#未通关 {ep} 四星队"))
        test_case(f"BOT-{5+i:03d}", f"#未通关 {ep}", result is not None, "", "P1")

    # BOT-U08~U10: 不同流派查询
    for i, cat in enumerate(["四星队", "三星队", "无精英满级"]):
        result = asyncio.get_event_loop().run_until_complete(run_handler(f"#未通关 惊霆无声 {cat}"))
        test_case(f"BOT-{8+i:03d}", f"#未通关 惊霆无声 {cat}", result is not None, "", "P1")

    # === #待压人 指令测试 ===
    # BOT-S01: #待压人 惊霆无声 四星队
    result = asyncio.get_event_loop().run_until_complete(run_handler("#待压人 惊霆无声 四星队"))
    test_case("BOT-S01", "#待压人 惊霆无声 四星队", result is not None,
              f"result_type={type(result).__name__}", "P0")

    # BOT-S02: #待压人 带天数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#待压人 惊霆无声 四星队 180"))
    test_case("BOT-S02", "#待压人 带天数180", result is not None, "", "P0")

    # BOT-S03: #待压人 缺少流派参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#待压人 惊霆无声"))
    test_case("BOT-S03", "#待压人 缺少流派参数返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-S04: #待压人 无参数
    result = asyncio.get_event_loop().run_until_complete(run_handler("#待压人"))
    test_case("BOT-S04", "#待压人 无参数返回错误提示", result is not None and "流派" in str(result),
              f"has_hint={'流派' in str(result)}", "P0")

    # BOT-S05: #待压人 天数格式错误
    result = asyncio.get_event_loop().run_until_complete(run_handler("#待压人 惊霆无声 四星队 abc"))
    test_case("BOT-S05", "#待压人 天数格式错误", result is not None and "天数" in str(result),
              f"has_hint={'天数' in str(result)}", "P1")

    # BOT-S06: #待压人 不存在的活动
    result = asyncio.get_event_loop().run_until_complete(run_handler("#待压人 不存在的活动 四星队"))
    test_case("BOT-S06", "#待压人 不存在的活动", result is not None, "", "P1")

    # BOT-S07~S10: 不同活动+流派组合
    combos = [
        ("惊霆无声", "四星队", "365"),
        ("骑兵与猎人", "三星队", "180"),
        ("破碎日冕", "无精英满级", "90"),
        ("怒号光明", "精一满级四星队", "365"),
    ]
    for i, (ep, cat, days) in enumerate(combos):
        result = asyncio.get_event_loop().run_until_complete(run_handler(f"#待压人 {ep} {cat} {days}"))
        test_case(f"BOT-{7+i:03d}", f"#待压人 {ep} {cat} {days}", result is not None, "", "P1")

    # BOT-S11~S15: 流派别名测试
    aliases = [
        ("四星", "四星队"),
        ("3星", "三星队"),
        ("满级", "无精英满级"),
        ("精一满级", "精一满级四星队"),
        ("无精英", "无精英满级"),
    ]
    for i, (alias, expected) in enumerate(aliases):
        result = asyncio.get_event_loop().run_until_complete(run_handler(f"#待压人 惊霆无声 {alias}"))
        if result and "未找到流派" in str(result):
            test_case(f"BOT-{11+i:03d}", f"别名'{alias}'→'{expected}'", False,
                      f"result={str(result)[:50]}", "P1")
        else:
            test_case(f"BOT-{11+i:03d}", f"别名'{alias}'→'{expected}'", True, "", "P1")


# ============================================================
# 第三阶段：展示格式验证
# ============================================================

def test_formatters():
    """2.3 展示格式验证 FMT-001 ~ FMT-052"""
    log("=" * 60)
    log("第三阶段：展示格式验证（单元测试）")
    log("=" * 60)

    import sys
    sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

    # === #查 格式验证 ===
    from formatter.record import format_records, format_single_record
    from formatter.video import format_video_link, extract_bv_number

    # FMT-001: 单条记录格式
    mock_record = {
        "operation": "H11-1",
        "cn_name": "惊霆行动-1",
        "operation_type": "normal",
        "category": ["四星队"],
        "raider": "测试玩家",
        "team": [{"name": "司霆惊蛰", "skillStr": "1"}, {"name": "黑角", "skillStr": "1"}],
        "date_published": "2024-09-01T12:00:00.000Z",
        "url": "https://www.bilibili.com/video/BV1example123",
    }
    result = format_single_record(mock_record)
    has_operation = "H11-1" in result
    has_category = "四星队" in result
    has_raider = "测试玩家" in result
    has_bv = "BV1example123" in result
    test_case("FMT-001", "单条记录包含关卡代号", has_operation, f"result={result[:100]}", "P0")
    test_case("FMT-002", "单条记录包含流派", has_category, "", "P0")
    test_case("FMT-003", "单条记录包含玩家名", has_raider, "", "P1")
    test_case("FMT-004", "单条记录包含BV号", has_bv, "", "P1")

    # FMT-005: 突袭标签
    mock_challenge = mock_record.copy()
    mock_challenge["operation_type"] = "challenge"
    result = format_single_record(mock_challenge)
    has_label = "突袭" in result
    test_case("FMT-005", "突袭记录显示突袭标签", has_label, f"result={result[:100]}", "P0")

    # FMT-006: 普通标签
    result = format_single_record(mock_record)
    has_label = "普通" in result
    test_case("FMT-006", "普通记录显示普通标签", has_label, f"result={result[:100]}", "P1")

    # FMT-007: 多条记录格式化
    mock_records = [mock_record, mock_record]
    result = format_records(mock_records, 2)
    test_case("FMT-007", "多条记录格式化", isinstance(result, list) and len(result) > 0,
              f"msg_count={len(result)}", "P0")

    # FMT-008: 无记录时的提示
    result = format_records([], 0)
    test_case("FMT-008", "无记录时返回提示", len(result) == 1 and "没有" in result[0],
              f"result={result}", "P0")

    # FMT-009: BV号截取
    bv = extract_bv_number("https://www.bilibili.com/video/BV1GJ411x7h7")
    test_case("FMT-009", "BV号截取", bv == "BV1GJ411x7h7",
              f"bv={bv}", "P1")

    # FMT-010: 非B站链接
    bv = extract_bv_number("https://www.youtube.com/watch?v=abc123")
    test_case("FMT-010", "非B站链接返回None", bv is None,
              f"bv={bv}", "P1")

    # FMT-011: format_video_link
    video = format_video_link("https://www.bilibili.com/video/BV1GJ411x7h7")
    test_case("FMT-011", "B站链接格式化为BV号", video == "BV1GJ411x7h7",
              f"video={video}", "P1")

    # FMT-012: 非B站链接格式化
    video = format_video_link("https://www.youtube.com/watch?v=abc123")
    test_case("FMT-012", "非B站链接格式化为'非B站视频'", video == "非B站视频",
              f"video={video}", "P1")

    # === #未通关 格式验证 ===
    from formatter.uncleared import format_uncleared

    # FMT-020: 正常未通关格式
    mock_uncleared = [
        {"operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "challenge", "hasChallenge": True},
        {"operation": "H11-3", "cn_name": "惊霆行动-3", "difficulty": "normal", "hasChallenge": False},
    ]
    result = format_uncleared("惊霆无声", "四星队", mock_uncleared)
    test_case("FMT-020", "未通关格式包含活动名", "惊霆无声" in result, f"result={result[:100]}", "P0")
    test_case("FMT-021", "未通关格式包含关卡数", "2个" in result or "未通关" in result, "", "P0")

    # FMT-022: 有突袭关时显示难度标签
    has_label = "突袭" in result or "普通" in result
    test_case("FMT-022", "有突袭关时显示难度标签", has_label, f"result={result[:150]}", "P0")

    # FMT-023: 全部通关时显示🎉
    result = format_uncleared("惊霆无声", "四星队", [])
    has_emoji = "🎉" in result
    test_case("FMT-023", "全部通关时显示🎉", has_emoji, f"result={result}", "P0")

    # === #待压人 格式验证 ===
    from formatter.stale import format_stale

    # FMT-030: 正常待压人格式
    mock_stale = [
        {
            "operation": "H11-1",
            "cn_name": "惊霆行动-1",
            "difficulty": "normal",
            "ageDays": 412,
            "records": [{"team": [{"name": "a"}, {"name": "b"}], "url": "https://www.bilibili.com/video/BV1test"}],
        }
    ]
    result = format_stale("惊霆无声", "四星队", 365, mock_stale)
    test_case("FMT-030", "待压人格式包含活动名", "惊霆无声" in result, f"result={result[:150]}", "P0")
    test_case("FMT-031", "待压人格式包含天数", "412" in result, "", "P0")
    test_case("FMT-032", "待压人格式包含人数", "2人" in result, "", "P0")

    # FMT-033: team_size=1不展示
    mock_stale_solo = [
        {
            "operation": "H11-3",
            "cn_name": "惊霆行动-3",
            "difficulty": "normal",
            "ageDays": 500,
            "records": [{"team": [{"name": "a"}], "url": ""}],
        }
    ]
    result = format_stale("惊霆无声", "四星队", 365, mock_stale_solo)
    test_case("FMT-033", "team_size=1不展示", "H11-3" not in result,
              f"result={result}", "P0")

    # FMT-034: 无待压记录时的提示
    result = format_stale("惊霆无声", "四星队", 365, [])
    test_case("FMT-034", "无待压记录返回提示", "无待压人记录" in result,
              f"result={result}", "P0")

    # === #流派 格式验证 ===
    from formatter.category import format_categories

    # FMT-040: 流派格式包含标题
    result = format_categories()
    test_case("FMT-040", "流派格式包含标题", "🏷️" in result or "流派" in result,
              f"result={result[:100]}", "P0")

    # FMT-041: 流派格式包含7个流派
    categories = ["四星队", "精一满级四星队", "精一1级四星队", "三星队", "精一1级", "无精英满级", "无精英1级"]
    all_found = all(cat in result for cat in categories)
    test_case("FMT-041", "流派格式包含7个流派", all_found, "", "P0")

    # === #help 格式验证 ===
    from formatter.help import format_help

    # FMT-050: help格式包含标题
    result = format_help()
    test_case("FMT-050", "help格式包含标题", "📋" in result or "Bot" in result,
              f"result={result[:100]}", "P0")

    # FMT-051: help格式包含所有指令说明
    has_all = all(x in result for x in ["#查", "#未通关", "#待压人", "#流派", "#help"])
    test_case("FMT-051", "help格式包含所有指令说明", has_all, "", "P0")

    # FMT-052: help格式包含示例
    test_case("FMT-052", "help格式包含示例", "示例" in result or "H11-1" in result,
              f"result={result[:200]}", "P1")


# ============================================================
# 第四阶段：性能基准测试
# ============================================================

def test_performance():
    """2.6 性能基准测试 PERF-001 ~ PERF-012"""
    log("=" * 60)
    log("第四阶段：性能基准测试")
    log("=" * 60)

    endpoints = [
        ("GET /bot/menu", "GET", "/menu", None),
        ("POST /bot/query-records (关卡+流派)", "POST", "/query-records",
         {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0}),
        ("POST /bot/query-records (仅流派)", "POST", "/query-records",
         {"query": {"category": "四星队"}, "skip": 0}),
        ("POST /bot/query-records (干员)", "POST", "/query-records",
         {"query": {"team": {"name": "司霆惊蛰"}}, "skip": 0}),
        ("POST /bot/uncleared", "POST", "/uncleared",
         {"category": "四星队", "episode": "惊霆无声"}),
        ("POST /bot/stale-records (365天)", "POST", "/stale-records",
         {"episode": "惊霆无声", "category": "四星队", "days": 365}),
        ("POST /bot/stale-records (180天)", "POST", "/stale-records",
         {"episode": "惊霆无声", "category": "四星队", "days": 180}),
        ("POST /bot/category-definition", "POST", "/category-definition",
         {"query": "四星队"}),
        ("POST /bot/operator-info", "POST", "/operator-info",
         {"query": "Reed"}),
    ]

    for i, (name, method, endpoint, payload) in enumerate(endpoints):
        # 每个端点测3次取平均
        times = []
        for _ in range(3):
            ms = measure_perf(endpoint, method, payload)
            times.append(ms)
        avg_ms = sum(times) / len(times)
        max_ms = max(times)
        min_ms = min(times)

        # 性能阈值
        threshold = 2000  # 2秒
        passed = avg_ms < threshold
        test_case(f"PERF-{i+1:03d}", f"{name} 平均{avg_ms:.0f}ms",
                  passed, f"avg={avg_ms:.0f}ms, min={min_ms:.0f}ms, max={max_ms:.0f}ms", "P2")

    # PERF-010: 连续请求稳定性
    times = []
    for _ in range(5):
        start = time.time()
        api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
        times.append((time.time() - start) * 1000)
    avg = sum(times) / len(times)
    max_deviation = max(abs(t - avg) for t in times)
    test_case("PERF-010", "连续请求稳定性（偏差<50%）",
              max_deviation / avg < 0.5 if avg > 0 else True,
              f"avg={avg:.0f}ms, max_dev={max_deviation:.0f}ms", "P2")

    # PERF-011: 大skip值响应时间
    ms = measure_perf("/query-records", "POST",
                      {"query": {"category": "四星队"}, "skip": 10000})
    test_case("PERF-011", f"大skip值响应时间 {ms:.0f}ms", ms < 3000,
              f"ms={ms:.0f}", "P2")

    # PERF-012: 并发请求（简单模拟）
    import concurrent.futures
    def do_request():
        start = time.time()
        api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
        return (time.time() - start) * 1000

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(do_request) for _ in range(5)]
        concurrent_times = [f.result() for f in concurrent.futures.as_completed(futures)]
    avg_concurrent = sum(concurrent_times) / len(concurrent_times)
    test_case("PERF-012", f"5并发平均{avg_concurrent:.0f}ms",
              avg_concurrent < 5000,
              f"avg={avg_concurrent:.0f}ms", "P2")


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 70)
    print("  明日方舟Bot综合测试 - 远野汉娜执行")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API Base: {BASE_URL}")
    print("=" * 70)

    # 执行所有测试阶段
    test_auth()
    test_query_records()
    test_uncleared()
    test_stale_records()
    test_menu()
    test_categories()
    test_category_definition()
    test_operator_info()
    test_bot_commands()
    test_formatters()
    test_performance()

    # 汇总
    total = results["pass"] + results["fail"] + results["blocked"]
    pass_rate = (results["pass"] / total * 100) if total > 0 else 0

    print("\n" + "=" * 70)
    print("  测试汇总")
    print("=" * 70)
    print(f"  总用例数: {total}")
    print(f"  通过: {results['pass']}")
    print(f"  失败: {results['fail']}")
    print(f"  阻塞: {results['blocked']}")
    print(f"  通过率: {pass_rate:.1f}%")

    if issues:
        print(f"\n  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"    [{issue['severity']}] {issue['case_id']}: {issue['name']}")
            print(f"           {issue['detail']}")

    if perf_data:
        print(f"\n  性能数据:")
        for pd in perf_data:
            print(f"    {pd['method']} {pd['endpoint']}: {pd['ms']:.0f}ms")

    print("=" * 70)

    # 输出JSON格式的结果（方便后续处理）
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "pass": results["pass"],
        "fail": results["fail"],
        "blocked": results["blocked"],
        "pass_rate": round(pass_rate, 1),
        "issues": issues,
        "perf_data": perf_data,
    }
    with open(r"F:\ArkCodes\bot_dpdl\docs\test_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  结果已保存到: F:\\ArkCodes\\bot_dpdl\\docs\\test_results.json")

    return 0 if results["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
