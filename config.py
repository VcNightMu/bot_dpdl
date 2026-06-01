# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: 配置管理 - 从环境变量加载Bot运行配置（NapCat/Wiki API/并发/消息长度等）
# 模型: mimo/mimo-v2.5

"""配置管理 - 从环境变量读取配置"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Bot配置"""
    # NapCat配置
    napcat_host: str = "napcat"
    napcat_port: int = 3001
    
    # FastAPI配置
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    
    # Wiki API配置
    wiki_base_url: str = "https://wiki.arkrec.com/v1/bot"
    wiki_api_token: str = ""
    
    # 并发控制
    wiki_max_concurrent: int = 10
    wiki_timeout_connect: float = 5.0
    wiki_timeout_read: float = 10.0
    
    # 消息配置
    max_msg_length: int = 800
    
    # 默认待压人天数
    default_stale_days: int = 365
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        return cls(
            napcat_host=os.getenv("NAPCAT_HOST", "napcat"),
            napcat_port=int(os.getenv("NAPCAT_PORT", "3001")),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8080")),
            wiki_base_url=os.getenv("WIKI_BASE_URL", "https://wiki.arkrec.com/v1/bot"),
            wiki_api_token=os.getenv("WIKI_API_TOKEN", ""),
            wiki_max_concurrent=int(os.getenv("WIKI_MAX_CONCURRENT", "10")),
            wiki_timeout_connect=float(os.getenv("WIKI_TIMEOUT_CONNECT", "5.0")),
            wiki_timeout_read=float(os.getenv("WIKI_TIMEOUT_READ", "10.0")),
            max_msg_length=int(os.getenv("MAX_MSG_LENGTH", "800")),
            default_stale_days=int(os.getenv("DEFAULT_STALE_DAYS", "365")),
        )


# 全局配置实例
config = Config.from_env()
