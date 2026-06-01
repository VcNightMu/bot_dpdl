"""api_client/client.py 单元测试。"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

_root = Path(r"F:\ArkCodes\bot_dpdl")

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
