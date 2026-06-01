# 少人WIKI 低配低练记录查询 Bot

基于 [少人Wiki](https://wiki.arkrec.com) 的 QQ 群 Bot，用于查询明日方舟低配低练通关记录。

## 功能

| 指令 | 说明 | 示例 |
|------|------|------|
| `#查 <关卡> <流派>` | 查询指定关卡的通关记录 | `#查 1-7 3星` |
| `#未通关 <活动名> <流派>` | 查询指定活动中未通关的关卡 | `#未通关 怀黍离 3星` |
| `#待压人 <活动名> <流派> [天数]` | 查询长时间未更新记录的关卡 | `#待压人 怀黍离 3星 180` |
| `#流派` | 查看所有可用流派列表 | `#流派` |
| `#help` | 显示帮助信息 | `#help` |

## 技术栈

- **Python 3.12+**
- **FastAPI** - Web 框架，接收 OneBot11 事件
- **httpx** - 异步 HTTP 客户端，调用 Wiki API
- **aiosqlite** - 异步 SQLite（缓存）
- **tenacity** - HTTP 请求重试机制
- **NapCat** - QQ 协议实现，推送 OneBot11 事件

## 项目结构

```
bot_dpdl/
├── main.py              # FastAPI 入口，接收 OneBot11 事件
├── config.py            # 配置管理（从环境变量加载）
├── requirements.txt     # Python 依赖
├── api_client/          # Wiki API 异步客户端
│   ├── client.py        # HTTP 封装 + 重试 + 并发控制
│   └── models.py        # 数据模型
├── resolver/            # 数据解析
│   ├── category.py      # 流派解析
│   ├── episode.py       # 章节解析
│   └── operation.py     # 关卡索引构建
├── formatter/           # 消息格式化
│   ├── record.py        # 通关记录格式化
│   ├── uncleared.py     # 未通关关卡格式化
│   ├── stale.py         # 待压人格式化
│   ├── category.py      # 流派列表格式化
│   ├── help.py          # 帮助信息格式化
│   └── video.py         # 视频链接格式化
├── qq_bot/              # QQ Bot 逻辑
│   ├── handler.py       # 指令路由与分发
│   ├── onebot.py        # OneBot11 适配器
│   └── commands/        # 指令处理
│       ├── query.py     # #查 指令
│       ├── uncleared.py # #未通关 指令
│       ├── stale.py     # #待压人 指令
│       ├── category.py  # #流派 指令
│       └── help.py      # #help 指令
└── tests/               # 测试
```

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
pytest tests/
```

### 项目约定

- 使用 `async/await` 进行异步编程
- HTTP 请求集成 tenacity 重试（最多 3 次，指数退避）
- 并发控制使用信号量（默认 10）
- 消息长度限制 800 字符（可通过 `MAX_MSG_LENGTH` 配置）

## 致谢

- [少人Wiki](https://wiki.arkrec.com) - 提供 API 支持
- [NapCat](https://napneko.github.io/) - QQ 协议实现
