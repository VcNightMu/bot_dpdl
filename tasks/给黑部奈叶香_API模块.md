<!-- 日期: 2026-06-01 -->
<!-- 开发者: 樱羽艾玛 -->
<!-- 功能: 给黑部奈叶香的任务分解，Wiki API模块 -->
<!-- 模型: mimo/mimo-v2.5 -->

# 给黑部奈叶香的任务：Wiki API模块

> 来源：樱羽艾玛（开发SE）| 日期：2026-06-01

## 你的任务

实现所有和少人wiki API（wiki.arkrec.com/bot）相关的模块。技术方案已全部确认（v1.2），请先阅读完整技术方案和API文档再动手。

**技术方案：** `F:\ArkCodes\bot_dpdl\docs\技术方案.md`
**API文档：** `F:\ArkCodes\bot_dpdl\docs\少人wiki_API.md`

## 你负责的模块

### 1. api_client/ — Wiki API封装

#### client.py
- 使用 httpx.AsyncClient（异步）
- 连接池配置：
  - max_connections=50
  - max_keepalive_connections=20
  - keepalive_expiry=30
- 超时配置：connect=5s, read=10s, write=5s, pool=5s
- 并发控制：asyncio.Semaphore(10)，限制同时对wiki的并发请求
- 重试策略（tenacity）：
  - 最多重试2次
  - 只对 TimeoutException 和 ConnectError 重试
  - 指数退避：min=1s, max=5s
- 封装以下端点的调用方法：
  - `GET /bot/menu` → 获取menu树
  - `POST /bot/query-records` → 按关卡+流派查记录
  - `POST /bot/uncleared` → 查未通关关卡
  - `POST /bot/stale-records` → 查待压人记录

#### models.py
```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class BotRecord:
    id: str
    raider: str
    url: str
    date_published: str
    story: str
    episode: str
    operation: str
    cn_name: str
    operation_type: str  # "normal" | "challenge"
    team: List[dict]
    category: List[str]
    group: str  # "" | "旧纪录"
    is_recommended: bool
    remark1: str = ""

@dataclass
class QueryResult:
    count: int
    count_valid: int
    records: List[BotRecord]

@dataclass
class UnclearedResult:
    episode: str
    category: str
    uncleared: List[dict]  # 每个包含 operation, cn_name, difficulty, has_challenge

@dataclass
class StaleResult:
    episode: str
    category: str
    days: int
    stale: List[dict]  # 每个包含 operation, cn_name, difficulty, has_challenge, min_team_size, latest_date, url
```

### 2. cache/ — SQLite缓存管理

#### db.py
- 使用 aiosqlite
- 启动时初始化：
  ```python
  PRAGMA journal_mode=WAL
  PRAGMA busy_timeout=5000
  ```
- 建表（如不存在）：
  ```sql
  CREATE TABLE menu_cache (
      id INTEGER PRIMARY KEY DEFAULT 1,
      data TEXT NOT NULL,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE operation_index (
      operation TEXT PRIMARY KEY,
      cn_name TEXT,
      episode TEXT,
      story TEXT,
      has_challenge BOOLEAN
  );
  ```

#### menu_cache.py
- `fetch_menu()`：调用API获取menu树
- `save_menu(data)`：写入SQLite + 重建operation_index
- `load_menu_index()`：从SQLite加载operation_index到内存（dict格式）
  ```python
  {
      "by_operation": {"H11-1": {...}, "M8-8": {...}},
      "by_cn_name": {"惊霆行动-1": {...}, "打磨利刃": {...}},
      "episodes": {"惊霆无声": [{"operation": "H11-1", ...}], ...}
  }
  ```
- `refresh_menu()`：版本更新后刷新，失败时降级使用旧缓存

## 注意事项

1. 代码放到 `F:\ArkCodes\bot_dpdl\src\` 目录下对应的子目录
2. 所有操作用 async/await
3. API的token通过环境变量 `WIKI_API_TOKEN` 传入，请求时放在Header中
4. 完成后写个简短的进度报告到 `C:\Users\Administrator\.qclaw\daily-reports\2026-06-01\progress-黑部奈叶香.md`
