import aiosqlite
import asyncio
from config import DATABASE_PATH
from database.schema import SCHEMA, SEED_SEASON

class Database:
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        self._conn = None
        self._lock = asyncio.Lock()

    async def connect(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.commit()
        await self._conn.execute(SEED_SEASON)
        await self._conn.commit()

    async def execute(self, query: str, *params):
        async with self._lock:
            await self._conn.execute(query, params)
            await self._conn.commit()

    async def fetchone(self, query: str, *params):
        async with self._conn.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetchall(self, query: str, *params):
        async with self._conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def close(self):
        if self._conn:
            await self._conn.close()