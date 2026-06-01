"""
检查400错误格式
"""
import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = 'https://wiki.arkrec.com/v1/bot'
HEADERS = {'Content-Type': 'application/json', 'X-Bot-Token': '23c85d451d3e5b1dacf2d74eb6397f2c00452430b169466b6664c1df428d128a'}

# Test 400 error format
resp = requests.post(f'{BASE_URL}/query-records', json={'query': {}}, headers=HEADERS, timeout=10)
print(f'Status: {resp.status_code}')
print(f'Content-Type: {resp.headers.get("Content-Type")}')
print(f'Raw response: {repr(resp.text)}')
try:
    data = resp.json()
    print(f'JSON parsed: {data}')
except Exception as e:
    print(f'JSON parse error: {e}')
    # Try to see what the actual bytes are
    print(f'Response bytes: {resp.content[:200]}')
