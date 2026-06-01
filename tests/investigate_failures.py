"""
调查失败用例
"""
import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = 'https://wiki.arkrec.com/v1/bot'
HEADERS = {'Content-Type': 'application/json', 'X-Bot-Token': '23c85d451d3e5b1dacf2d74eb6397f2c00452430b169466b6664c1df428d128a'}

print('=== 详细调查失败用例 ===')

# QR-008: 空query
print('\n--- QR-008: 空query ---')
resp = requests.post(f'{BASE_URL}/query-records', json={'query': {}}, headers=HEADERS, timeout=10)
print(f'状态码: {resp.status_code}')
print(f'响应体: {resp.text[:500]}')

# UC-003: 不存在的流派
print('\n--- UC-003: 不存在的流派 ---')
resp = requests.post(f'{BASE_URL}/uncleared', json={'category': '不存在的流派', 'episode': '惊霆无声'}, headers=HEADERS, timeout=10)
print(f'状态码: {resp.status_code}')
data = resp.json()
uncleared_list = data.get('uncleared', [])
print(f'uncleared数量: {len(uncleared_list)}')
if uncleared_list:
    print(f'第一个未通关: {json.dumps(uncleared_list[0], ensure_ascii=False)}')

# ERR-001: 400错误格式
print('\n--- ERR-001: 400错误格式 ---')
resp = requests.post(f'{BASE_URL}/query-records', json={'query': {}}, headers=HEADERS, timeout=10)
print(f'状态码: {resp.status_code}')
print(f'Content-Type: {resp.headers.get("Content-Type")}')
print(f'响应体: {resp.text[:200]}')

# 测试其他400错误场景
print('\n--- 其他400错误场景 ---')
resp = requests.post(f'{BASE_URL}/uncleared', json={}, headers=HEADERS, timeout=10)
print(f'缺少参数: 状态码={resp.status_code}, 响应={resp.text[:200]}')

resp = requests.post(f'{BASE_URL}/stale-records', json={}, headers=HEADERS, timeout=10)
print(f'stale-records缺少参数: 状态码={resp.status_code}, 响应={resp.text[:200]}')
