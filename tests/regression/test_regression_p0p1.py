"""
P0/P1问题回归验证 - 远野汉娜
"""
import requests
import json
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = 'https://wiki.arkrec.com/v1/bot'
BOT_TOKEN = '23c85d451d3e5b1dacf2d74eb6397f2c00452430b169466b6664c1df428d128a'
HEADERS = {'Content-Type': 'application/json', 'X-Bot-Token': BOT_TOKEN}

results = []

def api_post(endpoint, payload, timeout=10):
    url = f"{BASE_URL}{endpoint}"
    try:
        import time
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

def log(case_id, name, status, detail=""):
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    results.append({"id": case_id, "name": name, "status": status, "detail": detail})
    print(f"{icon} [{case_id}] {name}")
    if detail:
        print(f"   {detail}")

# ============================================================
# P0-1: 指令路由 - 无参数时返回错误提示
# ============================================================
print("=" * 60)
print("P0-1: 指令路由无参数回归验证")
print("=" * 60)

# 直接测试handler.py的正则匹配逻辑
from qq_bot.handler import CommandHandler
import asyncio

handler = CommandHandler()

async def test_handler(raw_msg):
    result = await handler.handle(raw_msg, group_id=0, user_id=0)
    return result

# P0-1a: #查 无参数
result = asyncio.run(test_handler("#查"))
if result and "缺少参数" in result and "格式" in result:
    log("P0-1a", "#查 无参数→错误提示", "PASS", f"返回: {result[:60]}")
else:
    log("P0-1a", "#查 无参数→错误提示", "FAIL", f"返回: {result}")

# P0-1b: #未通关 无参数
result = asyncio.run(test_handler("#未通关"))
if result and "缺少参数" in result:
    log("P0-1b", "#未通关 无参数→错误提示", "PASS", f"返回: {result[:60]}")
else:
    log("P0-1b", "#未通关 无参数→错误提示", "FAIL", f"返回: {result}")

# P0-1c: #待压人 无参数
result = asyncio.run(test_handler("#待压人"))
if result and "缺少参数" in result:
    log("P0-1c", "#待压人 无参数→错误提示", "PASS", f"返回: {result[:60]}")
else:
    log("P0-1c", "#待压人 无参数→错误提示", "FAIL", f"返回: {result}")

# P0-1d: #查 有参数（确保不影响正常功能）
result = asyncio.run(test_handler("#查 H11-1 四星队"))
if result and isinstance(result, list):
    log("P0-1d", "#查 有参数→正常查询", "PASS", f"返回{len(result)}条消息")
else:
    log("P0-1d", "#查 有参数→正常查询", "FAIL", f"返回: {str(result)[:80]}")

# P0-1e: #未通关 有参数
result = asyncio.run(test_handler("#未通关 惊霆无声 四星队"))
if result and isinstance(result, str) and "未通关" in result:
    log("P0-1e", "#未通关 有参数→正常查询", "PASS")
else:
    log("P0-1e", "#未通关 有参数→正常查询", "FAIL", f"返回: {str(result)[:80]}")

# P0-1f: #待压人 有参数
result = asyncio.run(test_handler("#待压人 惊霆无声 四星队"))
if result and isinstance(result, str):
    log("P0-1f", "#待压人 有参数→正常查询", "PASS")
else:
    log("P0-1f", "#待压人 有参数→正常查询", "FAIL", f"返回: {str(result)[:80]}")

# P0-1g: 空消息不匹配
result = asyncio.run(test_handler(""))
if result is None:
    log("P0-1g", "空消息→None", "PASS")
else:
    log("P0-1g", "空消息→None", "FAIL", f"返回: {result}")

# P0-1h: 普通消息不匹配
result = asyncio.run(test_handler("你好"))
if result is None:
    log("P0-1h", "普通消息→None", "PASS")
else:
    log("P0-1h", "普通消息→None", "FAIL", f"返回: {result}")

# ============================================================
# P0-2: #未通关 难度标签
# ============================================================
print("\n" + "=" * 60)
print("P0-2: #未通关难度标签回归验证")
print("=" * 60)

# P0-2a: 通过formatter验证 operation_index 传入
from formatter.uncleared import format_uncleared

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
if "[突袭]" in result:
    log("P0-2a", "formatter支持难度标签", "PASS", "包含[突袭]")
else:
    log("P0-2a", "formatter支持难度标签", "FAIL", f"输出: {result[:100]}")

# P0-2b: 通过API验证实际返回
resp = api_post("/uncleared", {"category": "四星队", "episode": "惊霆无声"})
if resp and resp.get("status_code") == 200:
    data = resp["json"]
    uncleared = data.get("uncleared", [])
    has_difficulty = all("difficulty" in item for item in uncleared)
    if has_difficulty:
        log("P0-2b", "API返回difficulty字段", "PASS", f"共{len(uncleared)}条，均含difficulty")
    else:
        log("P0-2b", "API返回difficulty字段", "FAIL")
else:
    log("P0-2b", "API返回difficulty字段", "FAIL", f"状态码: {resp.get('status_code') if resp else 'N/A'}")

# P0-2c: 验证uncleared.py传入operation_index
import inspect
from qq_bot.commands.uncleared import handle_uncleared
source = inspect.getsource(handle_uncleared)
if "operation_index" in source and "format_uncleared" in source:
    # 检查是否在调用format_uncleared时传入了operation_index
    if "format_uncleared(result.episode, result.category, result.uncleared, operation_index)" in source:
        log("P0-2c", "handle_uncleared传入operation_index", "PASS")
    else:
        log("P0-2c", "handle_uncleared传入operation_index", "FAIL", "未找到正确传参")
else:
    log("P0-2c", "handle_uncleared传入operation_index", "FAIL", "缺少operation_index")

# ============================================================
# P0-3: stale-records 过滤 team_size=1
# ============================================================
print("\n" + "=" * 60)
print("P0-3: stale-records team_size过滤回归验证")
print("=" * 60)

resp = api_post("/stale-records", {"episode": "惊霆无声", "category": "四星队", "days": 365})
if resp and resp.get("status_code") == 200:
    data = resp["json"]
    stale = data.get("stale", [])
    
    solo_count = 0
    for item in stale:
        for record in item.get("records", []):
            team = record.get("team", [])
            if len(team) <= 1:
                solo_count += 1
    
    if solo_count == 0:
        log("P0-3", "stale-records无team_size=1记录", "PASS", f"共{len(stale)}条stale，无solo记录")
    else:
        log("P0-3", "stale-records无team_size=1记录", "FAIL", f"发现{solo_count}条team_size<=1的记录")
else:
    log("P0-3", "stale-records无team_size=1记录", "FAIL", f"状态码: {resp.get('status_code') if resp else 'N/A'}")

# 验证formatter层过滤
from formatter.stale import format_stale
stale_with_solo = [
    {
        "operation": "H11-1", "cn_name": "惊霆行动-1", "difficulty": "normal",
        "ageDays": 400,
        "records": [{"team": [{"name": "单干员"}], "url": ""}]
    },
    {
        "operation": "H11-3", "cn_name": "惊霆行动-3", "difficulty": "normal",
        "ageDays": 350,
        "records": [{"team": [{"name": "干员A"}, {"name": "干员B"}], "url": ""}]
    }
]
result = format_stale("惊霆无声", "四星队", 365, stale_with_solo)
if "H11-1" not in result and "H11-3" in result:
    log("P0-3b", "formatter过滤team_size=1", "PASS", "solo记录被过滤，多人记录保留")
else:
    log("P0-3b", "formatter过滤team_size=1", "FAIL", f"输出: {result[:100]}")

# ============================================================
# P1-1: records 的 id 字段
# ============================================================
print("\n" + "=" * 60)
print("P1-1: records id字段回归验证")
print("=" * 60)

resp = api_post("/query-records", {"query": {"operation": "H11-1", "category": "四星队"}, "skip": 0})
if resp and resp.get("status_code") == 200:
    data = resp["json"]
    records = data.get("records", [])
    
    if records:
        first_record = records[0]
        has_id = "id" in first_record
        has__id = "_id" in first_record
        
        # 验证BotRecord.from_dict能正确解析
        from api_client.models import BotRecord
        bot_record = BotRecord.from_dict(first_record)
        
        if bot_record.id:
            log("P1-1", "BotRecord.id正确解析", "PASS", f"id={bot_record.id[:20]}...")
        else:
            log("P1-1", "BotRecord.id正确解析", "FAIL", f"id为空, API字段: id={has_id}, _id={has__id}")
    else:
        log("P1-1", "BotRecord.id正确解析", "FAIL", "无记录可验证")
else:
    log("P1-1", "BotRecord.id正确解析", "FAIL", f"状态码: {resp.get('status_code') if resp else 'N/A'}")

# ============================================================
# P1-2: operation 大小写不敏感（用户输入适配验证）
# 下游API是大小写敏感的，bot作为适配层需将用户输入归一化为大写
# 验证两层归一化：resolver.normalize_operation + client.query_records.upper()
# ============================================================
print("\n" + "=" * 60)
print("P1-2: operation大小写不敏感回归验证")
print("=" * 60)

# P1-2a: resolver层归一化验证
from resolver.operation import normalize_operation
test_cases = [
    ("h11-1", "H11-1"),
    ("H11-1", "H11-1"),
    ("m8-8", "M8-8"),
    ("gt-1", "GT-1"),
    ("H11-ex-1", "H11-EX-1"),
]
all_pass = True
for input_op, expected in test_cases:
    result = normalize_operation(input_op)
    if result != expected:
        log("P1-2a", f"resolver: {input_op}→{expected}", "FAIL", f"实际返回: {result}")
        all_pass = False
if all_pass:
    log("P1-2a", f"resolver归一化: {len(test_cases)}组用例全部通过", "PASS")

# P1-2b: client层upper()保护验证
import inspect
from api_client.client import WikiClient
src = inspect.getsource(WikiClient.query_records)
if 'operation.upper()' in src:
    log("P1-2b", "client层有operation.upper()保护", "PASS")
else:
    log("P1-2b", "client层有operation.upper()保护", "FAIL", "未找到.upper()调用")

# ============================================================
# 单元测试回归
# ============================================================
print("\n" + "=" * 60)
print("单元测试回归")
print("=" * 60)

import subprocess
ret = subprocess.run(
    ["python", "-m", "pytest", "tests/test_handler.py", "tests/test_command_query.py", 
     "tests/test_command_uncleared.py", "tests/test_command_stale.py", "tests/test_models.py", "-v", "--tb=short"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", cwd="F:\\ArkCodes\\bot_dpdl"
)
print(ret.stdout[-500:] if len(ret.stdout) > 500 else ret.stdout)
if ret.returncode == 0:
    log("UT-REG", "单元测试回归", "PASS")
else:
    log("UT-REG", "单元测试回归", "FAIL", f"exit code: {ret.returncode}")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("回归验证总结")
print("=" * 60)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
total = len(results)

print(f"总用例数: {total}")
print(f"通过: {passed}")
print(f"失败: {failed}")
print(f"通过率: {passed/total*100:.1f}%")

if failed > 0:
    print("\n失败用例:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  - [{r['id']}] {r['name']}: {r['detail']}")
