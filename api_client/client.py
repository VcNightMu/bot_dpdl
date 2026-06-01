# 日期: 2026-06-01
# 开发者: 黑部奈叶香
# 功能: 少人WIKI API异步HTTP客户端，封装所有API调用，集成重试和并发控制
# 模型: mimo/mimo-v2.5

"""少人WIKI API 异步客户端。

封装 wiki.arkrec.com/bot 的所有 HTTP 调用。
使用 httpx 异步客户端，集成 tenacity 重试和信号量并发控制。

技术方案参考：第二章（技术栈）、第七章（关卡名解析）
API 文档参考：少人wiki_API.md
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .models import (
    BotRecord,
    MenuStory,
    QueryResult,
    StaleResult,
    UnclearedResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 全局并发控制：信号量限制对 wiki API 的并发请求为 10
# ---------------------------------------------------------------------------
WIKI_SEMAPHORE: asyncio.Semaphore = asyncio.Semaphore(10)


class WikiAPIError(Exception):
    """Wiki API 调用异常基类。"""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class WikiAPIAuthError(WikiAPIError):
    """403 Token 失效。"""

    def __init__(self) -> None:
        super().__init__(403, "Bot认证失败，请联系管理员")


class WikiAPINotFoundError(WikiAPIError):
    """404 资源不存在。"""

    def __init__(self, resource: str, name: str) -> None:
        super().__init__(404, f"未找到: {resource} '{name}'")


class WikiAPIValidationError(WikiAPIError):
    """400 参数错误。"""

    def __init__(self, detail: str) -> None:
        super().__init__(400, f"请求参数有误: {detail}")


class WikiAPIServiceUnavailableError(WikiAPIError):
    """503 数据未导入。"""

    def __init__(self) -> None:
        super().__init__(503, "数据加载中，请稍后再试")


class WikiAPINetworkError(WikiAPIError):
    """网络超时或连接错误（重试耗尽后抛出）。"""

    def __init__(self, message: str = "网络波动，再试一次？") -> None:
        super().__init__(0, message)


# ---------------------------------------------------------------------------
# WikiClient — 异步 HTTP 客户端
# ---------------------------------------------------------------------------


class WikiClient:
    """少人WIKI API 异步客户端。

    用法::

        async with WikiClient(base_url="https://wiki.arkrec.com", token="...") as client:
            result = await client.query_records(operation="H11-1", category="四星队")
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 10.0,
        max_connections: int = 50,
        max_keepalive: int = 20,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._client: httpx.AsyncClient | None = None
        self._timeout = timeout
        self._max_connections = max_connections
        self._max_keepalive = max_keepalive

    # -- 生命周期 -----------------------------------------------------------

    async def __aenter__(self) -> WikiClient:
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def start(self) -> None:
        """启动 HTTP 客户端（应用启动时调用一次）。"""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(
                connect=5.0,
                read=self._timeout,
                write=5.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=self._max_connections,
                max_keepalive_connections=self._max_keepalive,
                keepalive_expiry=30,
            ),
        )
        logger.info("WikiClient started: base_url=%s", self._base_url)

    async def close(self) -> None:
        """关闭 HTTP 客户端（应用关闭时调用）。"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("WikiClient closed")

    # -- 底层请求 -----------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Bot-Token": self._token,
        }

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=5),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError)
        ),
        reraise=True,
    )
    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """带信号量 + 重试的 POST 请求。"""
        if not self._client:
            raise RuntimeError("WikiClient not started, call start() first")

        async with WIKI_SEMAPHORE:
            try:
                resp = await self._client.post(
                    path,
                    json=payload,
                    headers=self._build_headers(),
                )
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                # tenacity 会重试一次，两次都失败则抛出
                raise WikiAPINetworkError() from exc

            return self._handle_response(resp, path)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=5),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError)
        ),
        reraise=True,
    )
    async def _get(self, path: str) -> dict[str, Any]:
        """带信号量 + 重试的 GET 请求。"""
        if not self._client:
            raise RuntimeError("WikiClient not started, call start() first")

        async with WIKI_SEMAPHORE:
            try:
                resp = await self._client.get(
                    path,
                    headers=self._build_headers(),
                )
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                raise WikiAPINetworkError() from exc

            return self._handle_response(resp, path)

    @staticmethod
    def _handle_response(resp: httpx.Response, path: str) -> dict[str, Any]:
        """统一处理 HTTP 响应，抛出对应异常。"""
        if resp.status_code == 200:
            return resp.json()

        body = resp.text
        if resp.status_code == 400:
            raise WikiAPIValidationError(body)
        if resp.status_code == 403:
            raise WikiAPIAuthError()
        if resp.status_code == 404:
            raise WikiAPINotFoundError(path, body)
        if resp.status_code == 503:
            raise WikiAPIServiceUnavailableError()

        raise WikiAPIError(resp.status_code, f"Unexpected error: {body}")

    # -- 业务接口 -----------------------------------------------------------

    async def query_records(
        self,
        *,
        operation: str | None = None,
        category: str | None = None,
        cn_name: str | None = None,
        operation_type: str | None = None,
        team_name: str | None = None,
        team_skill: str | None = None,
        skip: int = 0,
    ) -> QueryResult:
        """查询攻略记录。

        对应 POST /bot/query-records。
        """
        query: dict[str, Any] = {}
        if team_name:
            query["team"] = {"name": team_name}
            if team_skill:
                query["team"]["skillStr"] = team_skill
        elif operation or category:
            if operation:
                query["operation"] = operation.upper()  # 归一化为大写，兼容后端大小写敏感
            if cn_name:
                query["cn_name"] = cn_name
            if category:
                query["category"] = category
            if operation_type:
                query["operationType"] = operation_type
        else:
            raise WikiAPIValidationError("query 必须包含至少一个查询条件")

        payload = {"query": query, "skip": skip}
        data = await self._post("/query-records", payload)
        return QueryResult.from_dict(data)

    async def uncleared(
        self,
        *,
        episode: str,
        category: str,
    ) -> UnclearedResult:
        """查询未通关关卡。

        对应 POST /bot/uncleared。
        """
        payload = {"episode": episode, "category": category}
        data = await self._post("/uncleared", payload)
        return UnclearedResult.from_dict(data)

    async def stale_records(
        self,
        *,
        episode: str,
        category: str,
        days: int = 365,
    ) -> StaleResult:
        """查询待压人记录。

        对应 POST /bot/stale-records。
        """
        payload = {
            "episode": episode,
            "category": category,
            "days": days,
        }
        data = await self._post("/stale-records", payload)
        
        # 过滤掉 team_size <= 1 的记录（后端未过滤，客户端补偿）
        if "stale" in data and isinstance(data["stale"], list):
            data["stale"] = [
                item for item in data["stale"]
                if len(item.get("records", [])) > 0
                and len(item["records"][0].get("team", [])) > 1
            ]
        
        return StaleResult.from_dict(data)

    async def get_menu(self) -> list[MenuStory]:
        """拉取精简版关卡树。

        对应 GET /bot/menu。返回 story 列表，用于构建 operation_index。
        """
        data = await self._get("/menu")
        return [MenuStory.from_dict(s) for s in data]
