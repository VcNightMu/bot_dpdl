"""cache/db.py 单元测试。

使用 :memory: SQLite 数据库。
"""

import sys
import types
import importlib.util
from pathlib import Path

import pytest

_root = Path(r"F:\ArkCodes\bot_dpdl")

def _make_pkg(name: str, path: Path) -> types.ModuleType:
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__path__ = [str(path)]
        m.__package__ = name
        sys.modules[name] = m
    return sys.modules[name]

_bot = _make_pkg("bot_dpdl", _root)
_cache_pkg = _make_pkg("cache", _root / "cache")
_cache_pkg.__package__ = "cache"
_bot.cache = _cache_pkg

_spec = importlib.util.spec_from_file_location(
    "cache.db", _root / "cache/db.py"
)
_mod = importlib.util.module_from_spec(_spec)
_mod.__package__ = "cache"
sys.modules["cache.db"] = _mod
_spec.loader.exec_module(_mod)

from cache.db import Database


class TestDatabase:
    @pytest.mark.asyncio
    async def test_init_creates_tables(self):
        db = Database(":memory:")
        await db.init()

        conn = db.connect()
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='menu_cache'"
        )
        assert await cursor.fetchone() is not None

        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='operation_index'"
        )
        assert await cursor.fetchone() is not None

        await db.close()

    @pytest.mark.asyncio
    async def test_connect_before_init_raises(self):
        db = Database(":memory:")
        with pytest.raises(RuntimeError, match="not initialized"):
            db.connect()

    @pytest.mark.asyncio
    async def test_close(self):
        db = Database(":memory:")
        await db.init()
        await db.close()
        assert db._db is None

    @pytest.mark.asyncio
    async def test_close_without_init(self):
        db = Database(":memory:")
        await db.close()

    @pytest.mark.asyncio
    async def test_menu_cache_table_operations(self):
        db = Database(":memory:")
        await db.init()
        conn = db.connect()

        await conn.execute(
            "INSERT OR REPLACE INTO menu_cache (id, data) VALUES (1, ?)",
            ('[{"story":"test"}]',),
        )
        await conn.commit()

        cursor = await conn.execute("SELECT data FROM menu_cache WHERE id = 1")
        row = await cursor.fetchone()
        assert row is not None
        assert row["data"] == '[{"story":"test"}]'

        await db.close()

    @pytest.mark.asyncio
    async def test_operation_index_table_operations(self):
        db = Database(":memory:")
        await db.init()
        conn = db.connect()

        await conn.execute(
            "INSERT INTO operation_index (operation, cn_name, episode, story, has_challenge) "
            "VALUES (?, ?, ?, ?, ?)",
            ("M8-8", "破碎日冕", "活动", "活动关卡", True),
        )
        await conn.commit()

        cursor = await conn.execute(
            "SELECT * FROM operation_index WHERE operation = 'M8-8'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["cn_name"] == "破碎日冕"
        assert row["has_challenge"] == 1

        await db.close()

    @pytest.mark.asyncio
    async def test_double_init(self):
        db = Database(":memory:")
        await db.init()
        await db.init()
        await db.close()
