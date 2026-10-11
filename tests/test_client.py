
import sys as _sys
from pathlib import Path as _Path

# 仓库根：由本文件位置推导，保证在任意路径/任意机器都能从当前仓库导入
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))

"""api_client/client.py 单元测试。"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

_root = _REPO_ROOT

# 加载 models
_spec_m = importlib.util.spec_from_file_location("api_client.models", _root / "api_client/models.py")
_mod_m = importlib.util.module_from_spec(_spec_m)
sys.modules["api_client.models"] = _mod_m
_spec_m.loader.exec_module(_mod_m)

# 加载 client
_spec_c = importlib.util.spec_from_file_location("api_client.client", _root / "api_client/client.py")
_mod_c = importlib.util.module_from_spec(_spec_c)
sys.modules["api_client.client"] = _mod_c
_spec_c.loader.exec_module(_mod_c)

from api_client.client import (
    WikiAPIAuthError,
    WikiAPINetworkError,
    WikiAPINotFoundError,
    WikiAPIValidationError,
    WikiClient,
    WikiAPIServiceUnavailableError,
)
from api_client.models import QueryResult, StaleResult, UnclearedResult, MenuStory


def _make_response(status_code=200, json_data=None, text=""):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text or str(json_data)
    resp.json.return_value = json_data or {}
    return resp


class TestWikiClientLifecycle:
    @pytest.mark.asyncio
    async def test_start_creates_client(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        assert client._client is None
        await client.start()
        assert client._client is not None
        await client.close()

    @pytest.mark.asyncio
    async def test_close(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        await client.close()
        assert client._client.is_closed

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with WikiClient(base_url="https://example.com", token="tok") as client:
            assert client._client is not None
        assert client._client.is_closed

    @pytest.mark.asyncio
    async def test_method_before_start_raises(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        with pytest.raises(RuntimeError, match="not started"):
            await client._post("/test", {})


class TestBuildHeaders:
    def test_headers_include_token(self):
        client = WikiClient(base_url="https://example.com", token="mytoken")
        headers = client._build_headers()
        assert headers["X-Bot-Token"] == "mytoken"
        assert headers["Content-Type"] == "application/json"


class TestHandleResponse:
    def test_200_returns_json(self):
        resp = _make_response(200, {"count": 5})
        result = WikiClient._handle_response(resp, "/test")
        assert result == {"count": 5}

    def test_400_raises_validation(self):
        resp = _make_response(400, text="bad param")
        with pytest.raises(WikiAPIValidationError):
            WikiClient._handle_response(resp, "/test")

    def test_403_raises_auth(self):
        resp = _make_response(403)
        with pytest.raises(WikiAPIAuthError):
            WikiClient._handle_response(resp, "/test")

    def test_404_raises_not_found(self):
        resp = _make_response(404, text="not here")
        with pytest.raises(WikiAPINotFoundError):
            WikiClient._handle_response(resp, "/test")

    def test_503_raises_service_unavailable(self):
        resp = _make_response(503)
        with pytest.raises(WikiAPIServiceUnavailableError):
            WikiClient._handle_response(resp, "/test")

    def test_unexpected_status_raises(self):
        resp = _make_response(418, text="teapot")
        with pytest.raises(Exception):
            WikiClient._handle_response(resp, "/test")


class TestQueryRecords:
    @pytest.mark.asyncio
    async def test_query_by_operation_and_category(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, {
            "count": 2, "countValid": 1,
            "records": [{"id": "r1", "raider": "A", "operation": "H11-1"}],
        })
        client._client.post = AsyncMock(return_value=mock_resp)

        result = await client.query_records(operation="H11-1", category="四星队")
        assert isinstance(result, QueryResult)
        assert result.count == 2
        assert len(result.records) == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_query_by_team(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, {"count": 1, "countValid": 1, "records": []})
        client._client.post = AsyncMock(return_value=mock_resp)

        await client.query_records(team_name="司霆惊蛰", team_skill="1")
        call_args = client._client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["query"]["team"]["name"] == "司霆惊蛰"
        assert payload["query"]["team"]["skillStr"] == "1"
        await client.close()

    @pytest.mark.asyncio
    async def test_query_no_params_raises(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        with pytest.raises(WikiAPIValidationError):
            await client.query_records()
        await client.close()

    @pytest.mark.asyncio
    async def test_query_403_raises_auth(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        client._client.post = AsyncMock(return_value=_make_response(403))
        with pytest.raises(WikiAPIAuthError):
            await client.query_records(operation="M8-8", category="四星队")
        await client.close()


class TestUncleared:
    @pytest.mark.asyncio
    async def test_uncleared_success(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, {
            "episode": "惊霆无声", "category": "四星队",
            "uncleared": [{"operation": "H11-1", "difficulty": "challenge"}],
        })
        client._client.post = AsyncMock(return_value=mock_resp)
        result = await client.uncleared(episode="惊霆无声", category="四星队")
        assert isinstance(result, UnclearedResult)
        assert result.episode == "惊霆无声"
        assert len(result.uncleared) == 1
        await client.close()


class TestStaleRecords:
    @pytest.mark.asyncio
    async def test_stale_success(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, {
            "episode": "惊霆无声", "category": "四星队", "days": 365,
            "stale": [{
                "operation": "H11-1", "ageDays": 400, "difficulty": "normal",
                "records": [{"team": [{"name": "干员A"}, {"name": "干员B"}], "url": ""}]
            }],
        })
        client._client.post = AsyncMock(return_value=mock_resp)
        result = await client.stale_records(episode="惊霆无声", category="四星队", days=365)
        assert isinstance(result, StaleResult)
        assert result.days == 365
        assert len(result.stale) == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_stale_default_days(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, {"stale": []})
        client._client.post = AsyncMock(return_value=mock_resp)
        await client.stale_records(episode="X", category="Y")
        call_args = client._client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["days"] == 365
        await client.close()

    @pytest.mark.asyncio
    async def test_stale_filters_solo_records(self):
        """team_size<=1 的记录被过滤"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, {
            "stale": [
                {"operation": "H11-1", "records": [{"team": [{"name": "单干员"}], "url": ""}]},
                {"operation": "H11-3", "records": [{"team": [{"name": "A"}, {"name": "B"}], "url": ""}]},
            ]
        })
        client._client.post = AsyncMock(return_value=mock_resp)
        result = await client.stale_records(episode="X", category="Y")
        assert len(result.stale) == 1
        assert result.stale[0]["operation"] == "H11-3"
        await client.close()


class TestGetMenu:
    @pytest.mark.asyncio
    async def test_get_menu(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        mock_resp = _make_response(200, [
            {"story": "活动关卡", "episodes": [
                {"episode": "骑兵与猎人", "operations": [
                    {"operation": "GT-1", "cn_name": "日正当中", "hasChallenge": False}
                ]},
            ]},
        ])
        client._client.get = AsyncMock(return_value=mock_resp)
        result = await client.get_menu()
        assert len(result) == 1
        assert isinstance(result[0], MenuStory)
        assert result[0].story == "活动关卡"
        assert result[0].episodes[0].operations[0].operation == "GT-1"
        await client.close()


class TestSearchRecordsPagination:
    """search_records(fetch_all=True) 的翻页行为。

    端点单页固定 80 条；实测活动可能超页（惊霆无声/精一1级 = 110 条），
    只取第一页会让上层本地统计漏数据。
    """

    @staticmethod
    def _fake_post(pages):
        """pages: {skip: [record_id, ...]}，并给出 count（取所有页总数）。"""
        total = sum(len(v) for v in pages.values())

        async def _post(path, payload):
            skip = payload.get("skip", 0)
            ids = pages.get(skip, [])
            return {
                "count": total,
                "countValid": total,
                "records": [
                    {"id": rid, "operation": f"OP-{rid}", "operationType": "normal",
                     "cn_name": "测试", "team": [{"name": "干员"}], "url": ""}
                    for rid in ids
                ],
            }
        return _post

    @pytest.mark.asyncio
    async def test_fetch_all_merges_pages(self):
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        pages = {0: [f"a{i}" for i in range(3)], 3: [f"b{i}" for i in range(2)]}
        client._post = self._fake_post(pages)

        result = await client.search_records(conditions=[{"field": "x", "value": "y"}], fetch_all=True)
        assert len(result.records) == 5
        assert result.count == 5
        await client.close()

    @pytest.mark.asyncio
    async def test_default_does_not_paginate(self):
        """默认只取第一页，不额外发请求"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        calls = []

        async def _post(path, payload):
            calls.append(payload.get("skip", 0))
            return {"count": 999, "countValid": 999,
                    "records": [{"id": "a1", "operation": "A-1", "team": [{"name": "x"}], "url": ""}]}

        client._post = _post
        result = await client.search_records(conditions=[{"field": "x", "value": "y"}])
        assert len(result.records) == 1
        assert calls == [0]
        await client.close()

    @pytest.mark.asyncio
    async def test_dedup_across_pages(self):
        """跨页重复 id 只保留一条，避免重复计数"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        client._post = self._fake_post({0: ["a1", "a2"], 2: ["a2", "a3"]})

        result = await client.search_records(conditions=[{"field": "x", "value": "y"}], fetch_all=True)
        ids = [r.id for r in result.records]
        assert ids == ["a1", "a2", "a3"]
        await client.close()

    @pytest.mark.asyncio
    async def test_respects_max_pages(self):
        """页数上限生效：count 很大时也不会无限翻页"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        calls = []

        async def _post(path, payload):
            calls.append(payload.get("skip", 0))
            n = len(calls)
            return {"count": 10000, "countValid": 10000,
                    "records": [{"id": f"p{n}_{i}", "operation": f"O-{n}", "team": [{"name": "x"}], "url": ""}
                                for i in range(2)]}

        client._post = _post
        result = await client.search_records(
            conditions=[{"field": "x", "value": "y"}], fetch_all=True, max_pages=3
        )
        assert len(calls) == 3          # 最多 3 页
        assert len(result.records) == 6
        await client.close()

    @pytest.mark.asyncio
    async def test_stops_when_page_empty(self):
        """某页返回空就停，不空转到上限"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        calls = []

        async def _post(path, payload):
            calls.append(payload.get("skip", 0))
            if payload.get("skip", 0) == 0:
                return {"count": 500, "countValid": 500,
                        "records": [{"id": "a1", "operation": "A-1", "team": [{"name": "x"}], "url": ""}]}
            return {"count": 500, "countValid": 500, "records": []}

        client._post = _post
        result = await client.search_records(conditions=[{"field": "x", "value": "y"}], fetch_all=True)
        assert len(calls) == 2
        assert len(result.records) == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_no_extra_request_when_single_page(self):
        """count 未超页时不翻页"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        calls = []

        async def _post(path, payload):
            calls.append(payload.get("skip", 0))
            return {"count": 2, "countValid": 2,
                    "records": [{"id": "a1", "operation": "A-1", "team": [{"name": "x"}], "url": ""},
                                {"id": "a2", "operation": "A-2", "team": [{"name": "x"}], "url": ""}]}

        client._post = _post
        result = await client.search_records(conditions=[{"field": "x", "value": "y"}], fetch_all=True)
        assert calls == [0]
        assert len(result.records) == 2
        await client.close()


class TestRetry:
    @pytest.mark.asyncio
    async def test_timeout_raises_network_error(self):
        """超时抛出 WikiAPINetworkError（内部 try/except 将 TimeoutException 转换）。"""
        client = WikiClient(base_url="https://example.com", token="tok")
        await client.start()
        client._client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with pytest.raises(WikiAPINetworkError):
            await client.query_records(operation="M8-8", category="四星队")
        await client.close()
