# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: FastAPI入口 - 接收OneBot11事件、路由指令、管理应用生命周期
# 模型: mimo/mimo-v2.5

"""FastAPI入口 + 启动逻辑"""
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件

from fastapi import FastAPI, Request

from config import config
from qq_bot.handler import CommandHandler
from qq_bot.onebot import OneBotAdapter
from api_client import WikiClient
from resolver.operation import build_operation_index
from resolver.episode_short import init_episode_short_map

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# 指令处理器
command_handler = CommandHandler()

# OneBot适配器
onebot_adapter: OneBotAdapter | None = None

# Wiki API客户端
wiki_client: WikiClient | None = None

# 关卡索引（启动时构建，供 format_uncleared 使用）
operation_index: dict | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global onebot_adapter, wiki_client
    
    # 启动时初始化
    logger.info("Bot启动中...")
    
    # 创建OneBot适配器
    onebot_adapter = OneBotAdapter(
        host=config.napcat_host,
        port=config.napcat_port
    )
    
    # 创建Wiki API客户端
    wiki_client = WikiClient(
        base_url=config.wiki_base_url,
        token=config.wiki_api_token
    )
    await wiki_client.start()
    
    # 构建关卡索引（供 format_uncleared 使用）
    global operation_index
    try:
        menu_data = await wiki_client.get_menu()
        # get_menu 返回 list[MenuStory]，需要转成 dict 格式
        menu_dicts = []
        for story in menu_data:
            story_dict = {
                "story": story.story,
                "episodes": []
            }
            for ep in story.episodes:
                ep_dict = {
                    "episode": ep.episode,
                    "operations": []
                }
                for op in ep.operations:
                    ep_dict["operations"].append({
                        "operation": op.operation,
                        "cn_name": op.cn_name,
                        "hasChallenge": op.has_challenge,
                    })
                story_dict["episodes"].append(ep_dict)
            menu_dicts.append(story_dict)
        operation_index = build_operation_index(menu_dicts)
        logger.info(f"关卡索引构建完成: {len(operation_index.get('by_operation', {}))} 个关卡")
        
        # 初始化活动缩写映射
        init_episode_short_map(operation_index)
        logger.info("活动缩写映射初始化完成")
    except Exception as e:
        logger.error(f"构建关卡索引失败: {e}")
        operation_index = None
    
    logger.info(f"Bot启动完成，监听 {config.api_host}:{config.api_port}")
    logger.info(f"NapCat地址: {config.napcat_host}:{config.napcat_port}")
    logger.info(f"Wiki API: {config.wiki_base_url}")
    
    yield
    
    # 关闭时清理
    logger.info("Bot关闭中...")
    if wiki_client:
        await wiki_client.close()
    if onebot_adapter:
        await onebot_adapter.close()
    logger.info("Bot已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="少人WIKI 低配低练记录查询Bot",
    description="基于 wiki.arkrec.com 的 QQ群 Bot",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/onebot")
async def receive_onebot_event(request: Request):
    """接收NapCat推送的onebot11事件"""
    try:
        event = await request.json()
    except Exception as e:
        logger.error(f"解析事件失败: {e}")
        return {"status": "error", "message": "invalid json"}
    
    # 只处理群消息
    if event.get("post_type") != "message":
        return {"status": "ok"}
    if event.get("message_type") != "group":
        return {"status": "ok"}
    
    # 提取消息（兼容字符串和OneBot11数组格式）
    raw_msg = event.get("message", "")
    if isinstance(raw_msg, list):
        # OneBot11数组格式: [{"type": "text", "data": {"text": "#流派"}}]
        parts = []
        for seg in raw_msg:
            if isinstance(seg, dict) and seg.get("type") == "text":
                parts.append(seg.get("data", {}).get("text", ""))
        raw_msg = "".join(parts)
    group_id = event.get("group_id")
    user_id = event.get("user_id")
    
    logger.info(f"收到群消息: group={group_id}, user={user_id}, msg={raw_msg[:50]}...")
    
    # 指令路由
    try:
        response = await command_handler.handle(raw_msg, group_id, user_id, operation_index)
        
        if response and onebot_adapter:
            # 发送响应消息
            messages = response if isinstance(response, list) else [response]
            for msg in messages:
                await onebot_adapter.send_group_msg(group_id, msg)
    except Exception as e:
        logger.error(f"处理指令失败: {e}", exc_info=True)
        if onebot_adapter:
            await onebot_adapter.send_group_msg(group_id, "Bot内部错误，请稍后重试")
    
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "bot-dpdl"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )
