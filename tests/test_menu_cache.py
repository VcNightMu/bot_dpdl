"""cache/menu_cache.py 单元测试。"""

import sys
import types
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

_root = Path(r"F:\ArkCodes\bot_dpdl")

def _make_pkg(name: str, path: Path) -> types.ModuleType:
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__path__ = [str(path)]
        sys.modules[name] = m
    return sys.modules[name]

_bot = _make_pkg("bot_dpdl", _root)
_api_pkg = _make_pkg("api_client", _root / "api_client")
_bot.api_client = _api_pkg

_spec_m = importlib.util.spec_from_file_location("api_client.models", _root / "api_client/models.py")
_mod_m = importlib.util.module_from_spec(_spec_m)
sys.modules["api_client.models"] = _mod_m
_spec_m.loader.exec_module(_mod_m)

_cache_pkg = _make_pkg("cache", _root / "cache")
_bot.cache = _cache_pkg

_spec_db = importlib.util.spec_from_file_location("cache.db", _root / "cache/db.py")
_mod_db = importlib.util.module_from_spec(_spec_db)
sys.modules["cache.db"] = _mod_db
_spec_db.loader.exec_module(_mod_db)

_spec_mc = importlib.util.spec_from_file_location("cache.menu_cache", _root / "cache/menu_cache.py")
_mod_mc = importlib.util.module_from_spec(_spec_mc)
_mod_mc.__package__ = "bot_dpdl.cache"
sys.modules["cache.menu_cache"] = _mod_mc
_spec_mc.loader.exec_module(_mod_mc)

from api_client.models import MenuEpisode, MenuOperation, MenuStory
from cache.db import Database
from cache.menu_cache import MenuCache


def _make_stories():
    return [
        MenuStory(
            story="活动关卡",
            episodes=[
                MenuEpisode(
                    episode="惊霆无声",
                    operations=[
                        MenuOperation(operation="H11-1", cn_name="惊霆行动-1", has_challenge=True),
                        MenuOperation(operation="H11-2", cn_name="惊霆行动-2", has_challenge=False),
                    ],
                )
            ],
        )
    ]


class TestMenuCache:
    @pytest_asyncio.fixture
    async def db(self):
        db = Database(":memory:")
        await db.init()
        yield db
        await db.close()

    @pytest.mark.asyncio
    async def test_load_from_db_empty(self, db):
        cache = MenuCache(db)
        result = await cache.load_from_db()
        assert result == []
        assert cache.stories == []

    @pytest.mark.asyncio
    async def test_save_and_load(self, db):
        cache = MenuCache(db)
        await cache.save_to_db(_make_stories())
        assert len(cache.stories) == 1

        cache2 = MenuCache(db)
        loaded = await cache2.load_from_db()
        assert len(loaded) == 1
        assert loaded[0].story == "活动关卡"
        assert loaded[0].episodes[0].operations[0].operation == "H11-1"

    @pytest.mark.asyncio
    async def test_save_overwrites(self, db):
        cache = MenuCache(db)
        await cache.save_to_db(_make_stories())
        await cache.save_to_db([MenuStory(story="主线关卡", episodes=[])])

        cache2 = MenuCache(db)
        loaded = await cache2.load_from_db()
        assert len(loaded) == 1
        assert loaded[0].story == "主线关卡"

    @pytest.mark.asyncio
    async def test_load_or_refresh_from_db(self, db):
        cache = MenuCache(db)
        await cache.save_to_db(_make_stories())
        mock_api = AsyncMock()

        cache2 = MenuCache(db)
        result = await cache2.load_or_refresh(mock_api)
        assert len(result) == 1
        mock_api.get_menu.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_or_refresh_from_api(self, db):
        cache = MenuCache(db)
        mock_api = AsyncMock()
        mock_api.get_menu.return_value = _make_stories()

        result = await cache.load_or_refresh(mock_api)
        assert len(result) == 1
        mock_api.get_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_success(self, db):
        cache = MenuCache(db)
        await cache.save_to_db(_make_stories())
        mock_api = AsyncMock()
        mock_api.get_menu.return_value = [MenuStory(story="新关卡", episodes=[])]

        result = await cache.refresh(mock_api)
        assert result[0].story == "新关卡"
        assert cache.stories[0].story == "新关卡"

    @pytest.mark.asyncio
    async def test_refresh_failure_keeps_old(self, db):
        cache = MenuCache(db)
        await cache.save_to_db(_make_stories())
        mock_api = AsyncMock()
        mock_api.get_menu.side_effect = Exception("network error")

        result = await cache.refresh(mock_api)
        assert len(result) == 1
        assert result[0].story == "活动关卡"

    @pytest.mark.asyncio
    async def test_stories_property(self, db):
        cache = MenuCache(db)
        assert cache.stories == []
        await cache.save_to_db(_make_stories())
        assert len(cache.stories) == 1
