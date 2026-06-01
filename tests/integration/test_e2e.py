# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: 端到端测试脚本 - 模拟OneBot消息验证完整链路
# 模型: mimo/mimo-v2.5

"""端到端测试 - 模拟 OneBot11 群消息，验证完整链路"""

import asyncio
import httpx
import json
import time
import sys
import io

# 修复 Windows 控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 测试配置
BASE_URL = "http://127.0.0.1:8080"
ONEBOT_ENDPOINT = f"{BASE_URL}/onebot"
HEALTH_ENDPOINT = f"{BASE_URL}/health"


def build_onebot_event(message: str, group_id: int = 123456, user_id: int = 654321) -> dict:
    """构建 OneBot11 群消息事件"""
    return {
        "post_type": "message",
        "message_type": "group",
        "group_id": group_id,
        "user_id": user_id,
        "message": message,
        "message_id": 10001,
        "message_seq": 1,
        "user_nickname": "测试用户",
    }


async def test_health(client: httpx.AsyncClient) -> bool:
    """测试健康检查端点"""
    print("🔍 测试健康检查端点...")
    try:
        resp = await client.get(HEALTH_ENDPOINT)
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ 健康检查通过: {data}")
            return True
        else:
            print(f"   ❌ 健康检查失败: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 健康检查异常: {e}")
        return False


async def test_onebot_message(client: httpx.AsyncClient, message: str, description: str) -> bool:
    """测试发送 OneBot 消息"""
    print(f"\n🔍 测试: {description}")
    print(f"   发送消息: {message}")
    
    event = build_onebot_event(message)
    start_time = time.time()
    
    try:
        resp = await client.post(ONEBOT_ENDPOINT, json=event)
        elapsed = time.time() - start_time
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ 请求成功 (HTTP {resp.status_code}, {elapsed:.2f}s)")
            print(f"   响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"   ❌ 请求失败: HTTP {resp.status_code}")
            print(f"   响应: {resp.text[:200]}")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ 请求异常 ({elapsed:.2f}s): {e}")
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 bot-dpdl 端到端测试")
    print("=" * 60)
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 健康检查
        health_ok = await test_health(client)
        results.append(("健康检查", health_ok))
        
        if not health_ok:
            print("\n❌ 服务未启动，请先运行: python main.py")
            return
        
        # 2. 测试 #查 指令
        query_ok = await test_onebot_message(
            client, 
            "#查 H11-1 四星队", 
            "#查 指令 - 查询关卡记录"
        )
        results.append(("#查指令", query_ok))
        
        # 3. 测试 #流派 指令
        category_ok = await test_onebot_message(
            client, 
            "#流派", 
            "#流派 指令 - 查看所有流派"
        )
        results.append(("#流派指令", category_ok))
        
        # 4. 测试 #help 指令
        help_ok = await test_onebot_message(
            client, 
            "#help", 
            "#help 指令 - 查看帮助"
        )
        results.append(("#help指令", help_ok))
        
        # 5. 测试非指令消息（应该不回复）
        normal_ok = await test_onebot_message(
            client, 
            "大家好", 
            "非指令消息 - 应该不触发回复"
        )
        results.append(("非指令消息", normal_ok))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {status} | {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查日志")


if __name__ == "__main__":
    asyncio.run(main())
