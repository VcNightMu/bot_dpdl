# 日期: 2026-06-01
# 开发者: 黑部奈叶香
# 功能: API客户端模块入口，统一导出WikiClient和相关模型类
# 模型: mimo/mimo-v2.5

"""少人WIKI API 客户端模块。

封装 wiki.arkrec.com/bot 的所有 HTTP 调用。
"""

from .client import (
    WikiClient,
    WikiAPIError,
    WikiAPIAuthError,
    WikiAPINotFoundError,
    WikiAPIValidationError,
    WikiAPIServiceUnavailableError,
    WikiAPINetworkError,
)
from .models import (
    BotRecord,
    MenuStory,
    MenuOperation,
    MenuEpisode,
    QueryResult,
    UnclearedResult,
    StaleResult,
)

__all__ = [
    "WikiClient",
    "WikiAPIError",
    "WikiAPIAuthError",
    "WikiAPINotFoundError",
    "WikiAPIValidationError",
    "WikiAPIServiceUnavailableError",
    "WikiAPINetworkError",
    "BotRecord",
    "MenuStory",
    "MenuOperation",
    "MenuEpisode",
    "QueryResult",
    "UnclearedResult",
    "StaleResult",
]
