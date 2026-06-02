# 日期: 2026-06-02
# 开发者: 橘雪莉
# 功能: OneBot11协议适配器 - 通过HTTP API与NapCat通信，发送群消息
# 模型: mimo/mimo-v2.5

"""OneBot11协议适配 - 与NapCat通信"""
import asyncio
import logging
import random

import httpx

logger = logging.getLogger(__name__)


class OneBotAdapter:
    """OneBot11协议适配器"""
    
    def __init__(self, host: str = "napcat", port: int = 3001):
        self.base_url = f"http://{host}:{port}"
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
        )
    
    async def send_group_msg(self, group_id: int, message: str) -> bool:
        """发送群消息"""
        try:
            # 随机延迟1-3秒，避免消息发送过快被风控
            delay = random.uniform(1.0, 3.0)
            logger.debug(f"发送延迟: {delay:.1f}s")
            await asyncio.sleep(delay)
            
            response = await self.client.post(
                f"{self.base_url}/send_group_msg",
                json={
                    "group_id": group_id,
                    "message": message
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("retcode") == 0:
                logger.info(f"消息发送成功: group={group_id}")
                return True
            else:
                logger.error(f"消息发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"发送群消息异常: {e}")
            return False
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
