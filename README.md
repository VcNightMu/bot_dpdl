# 少人WIKI 低配低练记录查询 Bot

基于 [少人Wiki](https://wiki.arkrec.com) 的 QQ 群 Bot，用于查询明日方舟低配低练通关记录。

## 功能

### 指令列表

| 指令 | 说明 | 示例 |
|------|------|------|
| `#查 <关卡> <流派>` | 查询指定关卡的通关记录 | `#查 H11-1 四星队` |
| `#人数 <关卡> [流派...]` | 查询关卡各流派的人数统计 | `#人数 M8-8 四星队 精一满级` |
| `#干员记录 <干员> <流派>` | 查询某干员在某流派的记录数 | `#干员记录 羽毛笔 无精英满级` |
| `#干员记录 <干员A>+<干员B>+... <流派>` | 查询多干员在流派同时上场的记录数（最多 13 个） | `#干员记录 羽毛笔+银灰 无精英满级` |
| `#未通关 <活动名> <流派>` | 查询指定活动中未通关的关卡 | `#未通关 怀黍离 四星队` |
| `#待压人 <活动名> <流派> [天数]` | 查询长时间未更新记录的关卡（默认 365 天） | `#待压人 怀黍离 四星队 180` |
| `#高难 <活动名> <流派> [人数]` | 查询该流派**人数达到阈值**才能通关的高难关卡（默认 10 人） | `#高难 巴别塔 四星队` / `#高难 惊霆无声 精一1级 6` |
| `#流派` | 查看所有可用流派列表 | `#流派` |
| `#help` | 显示帮助信息 | `#help` |

### 高级特性

**高难查询** — `#高难` 列出「该关在该流派下，**最少人记录也需达到指定人数**」的关卡：

- 人数可省略（默认 **10**），也可自定，取值 **1–13**
- **不同流派的人数基数差别很大**：例如「精一1级」几乎没有 10 人以上的图，
  该流派可以用更小的阈值，如 `#高难 惊霆无声 精一1级 6`
- 展示每关的最少人数、记录条数与可达视频链接
- 普通/突袭**独立判定**（同一关的突袭可能比普通更难）
- 阈值上限与默认值定义在 `resolver/high_difficulty.py` 与
  `qq_bot/commands/high_difficulty.py` 的 `MAX_THRESHOLD` / `HIGH_TEAM_THRESHOLD`
- 注意：「最少 N 人」与「存在 N 人记录」是两回事。前者要求最优成绩就要 N 人；
  后者只说明有人用 N 人打过。本功能采用**前者**

**活动缩写查询** — `#未通关` / `#待压人` / `#高难` 支持缩写：

- 主线章节：`#未通关 第五章 四星队` 或 `#未通关 5 四星队`
- 活动代号：`#未通关 SV 四星队`
- 缩写对应多个活动时会提示选择

**剿灭作战聚合查询** — 剿灭关卡统一视为「剿灭」活动，不区分长期/轮换委托：

- 活动级：`#未通关 剿灭 四星队` / `#待压人 剿灭 四星队`
- 关卡级：`#查 多索雷斯换水口 四星队`（直接输关卡中文名）

**关卡中文名查询** — `#查` / `#人数` 支持直接用关卡中文名（如剿灭关卡的「多索雷斯换水口」）。

**预设流派** — `#干员记录` 只支持预设的低配低练流派（共 9 个，含别名）：

> 四星队、精一满级四星队、精一1级四星队、三星队、精一1级、精一满级、精二1级五星队、无精英满级、无精英1级

支持别名归一化，例如 `四星`→`四星队`、`无精英`→`无精英满级`、`3星`→`三星队` 等。

**干员组合查询** — `#干员记录` 支持用 `+` 连接多个干员，查询同时上场的记录：

- `#干员记录 羽毛笔+银灰 无精英满级` — 查羽毛笔和银灰在无精英满级同时上场的记录
- 支持任意多个干员（最多 13 个），按 AND（同时在场）检索，且限定流派
- 组合中的干员名同样支持中/英/日名和别名

## 技术栈

- **Python 3.12+**
- **FastAPI** - Web 框架，接收 OneBot11 事件
- **httpx** - 异步 HTTP 客户端，调用 Wiki API
- **aiosqlite** - 异步 SQLite（本地缓存）
- **tenacity** - HTTP 请求重试机制
- **NapCat** - QQ 协议实现，推送 OneBot11 事件

## 项目结构

```
bot_dpdl/
├── main.py              # FastAPI 入口，接收 OneBot11 事件
├── config.py            # 配置管理（从环境变量加载）
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板（cp .env.example .env）
├── api_client/          # Wiki API 异步客户端
│   ├── client.py        # HTTP 封装 + 重试 + 并发控制
│   └── models.py        # 数据模型
├── resolver/            # 数据解析
│   ├── category.py      # 流派解析（9 个预设流派 + 别名）
│   ├── command_args.py  # 指令参数统一解析（多余参数 / 天数数字冲突）
│   ├── duplicate.py     # 重复关卡代号检测
│   ├── episode.py       # 章节/活动解析（含剿灭聚合）
│   ├── episode_short.py # 活动缩写映射
│   └── operation.py     # 关卡索引构建
├── formatter/           # 消息格式化
│   ├── category.py      # 流派列表格式化
│   ├── help.py          # 帮助信息格式化
│   ├── operation_info.py # #人数 格式化
│   ├── record.py        # 通关记录格式化
│   ├── stale.py         # 待压人格式化
│   ├── uncleared.py     # 未通关格式化
│   └── video.py         # 视频链接格式化
├── qq_bot/              # QQ Bot 逻辑
│   ├── handler.py       # 指令路由与分发
│   ├── onebot.py        # OneBot11 适配器
│   └── commands/        # 指令处理
│       ├── query.py     # #查
│       ├── operation_info.py # #人数
│       ├── operator_records.py # #干员记录
│       ├── uncleared.py # #未通关
│       ├── stale.py     # #待压人
│       ├── category.py  # #流派
│       └── help.py      # #help
├── tests/               # 单元测试（pytest 可直接整目录运行）
├── tools/               # 手工/线上检查脚本（不参与 pytest 收集）
├── api_test/            # Wiki API 连通性/契约测试脚本
├── docs/                # 文档（注意：被 .gitignore 忽略，不进版本控制）
├── tasks/               # 历史任务文档（已失效，仅留档）
└── docker-compose.yml / Dockerfile
```

> `cache/` 已删除：它是从未被生产代码引用的死代码（相对导入写法本身也跑不起来），
> 项目当前**不使用 SQLite**，启动时实时拉取 menu 并在内存建索引。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

主要配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NAPCAT_HOST` | NapCat 服务地址 | `napcat` |
| `NAPCAT_PORT` | NapCat 服务端口 | `3001` |
| `API_HOST` | Bot 监听地址 | `0.0.0.0` |
| `API_PORT` | Bot 监听端口 | `8080` |
| `WIKI_BASE_URL` | Wiki API 地址 | `https://wiki.arkrec.com/v1/bot` |
| `WIKI_API_TOKEN` | Wiki API Token | - |
| `DEFAULT_STALE_DAYS` | 待压人默认天数 | `365` |
| `MAX_MSG_LENGTH` | 消息最大长度 | `800` |

### 3. 启动 Bot

```bash
python main.py
```

Bot 将在 `http://0.0.0.0:8080` 启动，接收 NapCat 推送的 OneBot11 事件。

### 4. Docker 部署（可选）

```bash
docker-compose up -d
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/onebot` | POST | 接收 OneBot11 事件 |
| `/health` | GET | 健康检查 |

## 开发

### 运行测试

```bash
# 单元测试（372 passed，可整目录运行）
pytest tests/
```

`tools/` 下是**手工/线上检查脚本**（打真实 Wiki API，需要网络与 Token），
不参与 pytest 收集，按需单独运行：

| 脚本 | 用途 |
|------|------|
| `tools/e2e_smoke.py` | 对本地 `127.0.0.1:8080` 发 OneBot 事件做端到端冒烟 |
| `tools/api_comprehensive_check.py` | 打线上 API 的全量契约/连通性检查 |
| `tools/formatter_check.py` | 单独的 formatter 输出检查 |

### 项目约定

- 使用 `async/await` 进行异步编程
- HTTP 请求集成 tenacity 重试（最多 2 次，指数退避）
- 并发控制使用信号量（默认 10）
- 消息长度限制 800 字符。⚠️ 该值**目前硬编码在 `formatter/record.py`**，
  `MAX_MSG_LENGTH` 环境变量虽已定义但尚未接线，改 `.env` 暂不生效
- Git 提交信息格式：`type: 描述 - [开发者:名字] [模型:模型名]`

## 致谢

- [少人Wiki](https://wiki.arkrec.com) - 提供 API 支持
- [NapCat](https://napneko.github.io/) - QQ 协议实现
