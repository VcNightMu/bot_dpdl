# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: onebot.py 单元测试 - 验证OneBot11协议适配器的消息发送
# 模型: mimo/mimo-v2.5

"""onebot.py 单元测试"""

import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from qq_bot.onebot import OneBotAdapter


@pytest.fixture
def adapter():
    """创建 OneBotAdapter 实例（mock httpx）"""
    with patch("qq_bot.onebot.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        adapter = OneBotAdapter(host="test-host", port=3001)
        adapter._client = mock_client  # 注入 mock 客户端
        yield adapter, mock_client


class TestInit:
    """测试初始化"""

    def test_base_url(self):
        """验证 base_url 构造"""
        with patch("qq_bot.onebot.httpx.AsyncClient"):
            adapter = OneBotAdapter(host="myhost", port=1234)
            assert adapter.base_url == "http://myhost:1234"

    def test_default_values(self):
        """验证默认参数"""
        with patch("qq_bot.onebot.httpx.AsyncClient"):
            adapter = OneBotAdapter()
            assert adapter.base_url == "http://napcat:3001"


class TestSendGroupMsg:
    """测试 send_group_msg"""

    @pytest.mark.asyncio
    async def test_send_success(self, adapter):
        """发送成功返回 True"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        result = await adj.send_group_msg(group_id=12345, message="测试消息")
        assert result is True
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_failure_retcode(self, adapter):
        """retcode 非 0 返回 False"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 1, "msg": "failed"}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        result = await adj.send_group_msg(group_id=12345, message="测试消息")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_http_error(self, adapter):
        """HTTP 错误返回 False"""
        adj, mock_client = adapter
        mock_client.post = AsyncMock(side_effect=Exception("网络错误"))

        result = await adj.send_group_msg(group_id=12345, message="测试消息")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_request_payload(self, adapter):
        """验证发送的请求 payload 格式"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        await adj.send_group_msg(group_id=99999, message="Hello")
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["group_id"] == 99999
        assert call_args[1]["json"]["message"] == "Hello"


class TestClose:
    """测试关闭"""

    @pytest.mark.asyncio
    async def test_close(self):
        """关闭时调用 aclose"""
        with patch("qq_bot.onebot.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            adapter = OneBotAdapter()
            adapter._client = mock_client
            await adapter.close()
            mock_client.aclose.assert_called_once()
