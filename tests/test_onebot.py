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


class TestSendDelay:
    """测试发送前随机延迟（防风控）"""

    @pytest.mark.asyncio
    async def test_delay_is_called(self, adapter):
        """验证 asyncio.sleep 被调用（存在延迟）"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("qq_bot.onebot.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await adj.send_group_msg(group_id=12345, message="测试延迟")
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_delay_range(self, adapter):
        """验证延迟时间在 1-3 秒范围内"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("qq_bot.onebot.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await adj.send_group_msg(group_id=12345, message="测试范围")
            delay = mock_sleep.call_args[0][0]
            assert 1.0 <= delay <= 3.0, f"延迟 {delay}s 不在 1-3 秒范围内"

    @pytest.mark.asyncio
    async def test_delay_success_result(self, adapter):
        """验证延迟不影响成功返回值"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("qq_bot.onebot.asyncio.sleep", new_callable=AsyncMock):
            result = await adj.send_group_msg(group_id=12345, message="测试成功")
        assert result is True

    @pytest.mark.asyncio
    async def test_delay_failure_result(self, adapter):
        """验证延迟不影响失败返回值"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 1, "msg": "failed"}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("qq_bot.onebot.asyncio.sleep", new_callable=AsyncMock):
            result = await adj.send_group_msg(group_id=12345, message="测试失败")
        assert result is False

    @pytest.mark.asyncio
    async def test_delay_before_request(self, adapter):
        """验证延迟在 HTTP 请求之前执行"""
        adj, mock_client = adapter
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retcode": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_resp)

        call_order = []
        async def fake_sleep(s):
            call_order.append("sleep")
        async def fake_post(*args, **kwargs):
            call_order.append("post")
            return mock_resp

        with patch("qq_bot.onebot.asyncio.sleep", side_effect=fake_sleep):
            mock_client.post = AsyncMock(side_effect=fake_post)
            await adj.send_group_msg(group_id=12345, message="测试顺序")
        assert call_order == ["sleep", "post"], f"执行顺序错误: {call_order}"


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
