# 日期: 2026-06-01
# 开发者: 橘雪莉
# 功能: config.py 单元测试 - 验证配置管理模块的默认值和环境变量加载
# 模型: mimo/mimo-v2.5

"""config.py 单元测试"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, r"F:\ArkCodes\bot_dpdl")

from config import Config


class TestConfigDefaults:
    """测试 Config 默认值"""

    def test_default_napcat_host(self):
        cfg = Config()
        assert cfg.napcat_host == "napcat"

    def test_default_napcat_port(self):
        cfg = Config()
        assert cfg.napcat_port == 3001

    def test_default_api_host(self):
        cfg = Config()
        assert cfg.api_host == "0.0.0.0"

    def test_default_api_port(self):
        cfg = Config()
        assert cfg.api_port == 8080

    def test_default_wiki_base_url(self):
        cfg = Config()
        assert cfg.wiki_base_url == "https://wiki.arkrec.com/v1/bot"

    def test_default_wiki_api_token(self):
        cfg = Config()
        assert cfg.wiki_api_token == ""

    def test_default_max_concurrent(self):
        cfg = Config()
        assert cfg.wiki_max_concurrent == 10

    def test_default_max_msg_length(self):
        cfg = Config()
        assert cfg.max_msg_length == 800

    def test_default_stale_days(self):
        cfg = Config()
        assert cfg.default_stale_days == 365


class TestConfigFromEnv:
    """测试 Config.from_env() 从环境变量加载"""

    def test_from_env_defaults(self):
        """没有设置环境变量时使用默认值"""
        with patch.dict(os.environ, {}, clear=True):
            cfg = Config.from_env()
            assert cfg.napcat_host == "napcat"
            assert cfg.napcat_port == 3001
            assert cfg.api_port == 8080
            assert cfg.wiki_base_url == "https://wiki.arkrec.com"
            assert cfg.wiki_api_token == ""

    def test_from_env_custom_values(self):
        """环境变量设置了值时使用环境变量的值"""
        env = {
            "NAPCAT_HOST": "my-napcat",
            "NAPCAT_PORT": "3002",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "WIKI_BASE_URL": "https://custom-wiki.com/v1/bot",
            "WIKI_API_TOKEN": "my-secret-token",
            "WIKI_MAX_CONCURRENT": "20",
            "WIKI_TIMEOUT_CONNECT": "3.0",
            "WIKI_TIMEOUT_READ": "15.0",
            "MAX_MSG_LENGTH": "1000",
            "DEFAULT_STALE_DAYS": "180",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config.from_env()
            assert cfg.napcat_host == "my-napcat"
            assert cfg.napcat_port == 3002
            assert cfg.api_host == "127.0.0.1"
            assert cfg.api_port == 9000
            assert cfg.wiki_base_url == "https://custom-wiki.com/v1/bot"
            assert cfg.wiki_api_token == "my-secret-token"
            assert cfg.wiki_max_concurrent == 20
            assert cfg.wiki_timeout_connect == 3.0
            assert cfg.wiki_timeout_read == 15.0
            assert cfg.max_msg_length == 1000
            assert cfg.default_stale_days == 180

    def test_from_env_partial_override(self):
        """只设置部分环境变量，其余用默认值"""
        env = {
            "NAPCAT_HOST": "custom-host",
            "API_PORT": "5000",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config.from_env()
            assert cfg.napcat_host == "custom-host"
            assert cfg.api_port == 5000
            assert cfg.napcat_port == 3001  # 默认值
            assert cfg.wiki_api_token == ""  # 默认值
