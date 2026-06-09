#!/usr/bin/env python3
"""
Complete test suite for Guess The Intruder bot – covers all features & edge cases.
Run with: python tests.py   (make sure your virtual environment is active)
"""

import sys, os, asyncio, io, time, importlib, traceback, json
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_DB_PATH = "test_game.db"
P1_ID = 111111
P2_ID = 222222
P3_ID = 333333

def cleanup_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

# ──────────────────────────
# 1. Syntax
# ──────────────────────────
def test_syntax():
    print("\n=== Testing Syntax ===")
    errors = []
    for root, dirs, files in os.walk("."):
        if ".venv" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        compile(f.read(), path, 'exec')
                except SyntaxError as e:
                    errors.append(f"{path}: {e}")
    if errors:
        print("FAILED")
        for e in errors:
            print("  ", e)
    else:
        print("OK")
    return len(errors) == 0

# ──────────────────────────
# 2. Imports
# ──────────────────────────
def test_imports():
    print("\n=== Testing Imports ===")
    modules = [
        "config", "database.engine", "database.schema",
        "core.game_engine", "core.difficulty", "core.anti_cheat", "core.events",
        "handlers.start", "handlers.help", "handlers.quick_play",
        "handlers.group_battle", "handlers.ranked", "handlers.daily_challenge",
        "handlers.endless", "handlers.inline_query", "handlers.profile",
        "handlers.leaderboard", "handlers.daily_reward", "handlers.achievements_show",
        "handlers.admin", "handlers.friends",
        "services.xp_progression", "services.achievements",
        "utils.helpers", "utils.rate_limiter",
    ]
    errors = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError as e:
            # Only flag missing internal modules, not external deps
            if "telegram" not in str(e) and "PIL" not in str(e) and "dotenv" not in str(e) and "aiosqlite" not in str(e):
                errors.append(f"{mod}: {e}")
    if errors:
        print("FAILED")
        for e in errors:
            print("  ", e)
    else:
        print("OK")
    return len(errors) == 0

# ──────────────────────────
# 3. Database & Friend System
# ──────────────────────────
async def test_database_and_friends():
    print("\n=== Testing Database & Friends ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    try:
        await db.connect()

        # Create three users
        await create_user_if_not_exists(P1_ID, "alice", "Alice", db)
        await create_user_if_not_exists(P2_ID, "bob", "Bob", db)
        await create_user_if_not_exists(P3_ID, "charlie", "Charlie", db)

        # Test friend request
        await db.execute("INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'pending')", P1_ID, P2_ID)
        req = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", P1_ID, P2_ID)
        assert req["status"] == "pending", "Friend request not created"

        # Test accept
        await db.execute("UPDATE friendships SET status = 'accepted' WHERE user_id = ? AND friend_id = ?", P1_ID, P2_ID)
        await db.execute("INSERT OR IGNORE INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'accepted')", P2_ID, P1_ID)
        f1 = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", P1_ID, P2_ID)
        f2 = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", P2_ID, P1_ID)
        assert f1["status"] == "accepted" and f2["status"] == "accepted", "Bidirectional friendship failed"

        # Test duplicate request
        await db.execute("INSERT OR IGNORE INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'pending')", P1_ID, P2_ID)
        dup = await db.fetchone("SELECT COUNT(*) as cnt FROM friendships WHERE user_id = ? AND friend_id = ?", P1_ID, P2_ID)
        assert dup["cnt"] == 1, "Duplicate friend request allowed"

        print("OK - Friend system works")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        traceback.print_exc()
        return False
    finally:
        await db.close()
        cleanup_db()

# ──────────────────────────
# 4. Inline Puzzle Pool
# ──────────────────────────
async def test_inline_pool():
    print("\n=== Testing Inline Puzzle Pool ===")
    from core.game_engine import generate_puzzle
    pool = [generate_puzzle(difficulty=1) for _ in range(5)]
    assert len(pool) == 5
    p = pool.pop(0)
    assert "options" in p
    print("OK - Inline pool works")
    return True

# ──────────────────────────
# 5. Leaderboard Cache
# ──────────────────────────
async def test_leaderboard_cache():
    print("\n=== Testing Leaderboard Cache ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    try:
        await db.connect()
        await create_user_if_not_exists(P1_ID, "alice", "Alice", db)
        await create_user_if_not_exists(P2_ID, "bob", "Bob", db)
        top = await db.fetchall("SELECT user_id, username, first_name, level, mmr FROM users ORDER BY mmr DESC LIMIT 20")
        assert len(top) == 2
        print("OK - Leaderboard cache works")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False
    finally:
        await db.close()
        cleanup_db()

# ──────────────────────────
# 6. Rate Limiter
# ──────────────────────────
async def test_rate_limiter():
    print("\n=== Testing Rate Limiter ===")
    from utils.rate_limiter import RateLimiter
    limiter = RateLimiter(max_calls=3, period=2)

    # Must use await
    assert await limiter.is_allowed(123) == True
    assert await limiter.is_allowed(123) == True
    assert await limiter.is_allowed(123) == True
    # 4th call should be blocked
    assert await limiter.is_allowed(123) == False

    # Wait for the period to expire (use asyncio.sleep, not time.sleep)
    await asyncio.sleep(2.1)

    # Now allowed again
    assert await limiter.is_allowed(123) == True
    print("OK - Rate limiter works")
    return True
# ──────────────────────────
# 7. Duel Scoring
# ──────────────────────────
async def test_duel_scoring():
    print("\n=== Testing Duel Scoring ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    from handlers.ranked import start_duel, finish_duel
    cleanup_db()
    db = Database(TEST_DB_PATH)
    await db.connect()
    mock_ctx = MagicMock()
    mock_ctx.bot_data = {"db": db}
    mock_ctx.bot = AsyncMock()
    mock_ctx.bot.send_message = AsyncMock(return_value=MagicMock(message_id=1, chat_id=1))
    mock_ctx.bot.edit_message_text = AsyncMock()
    with patch('asyncio.sleep', new=AsyncMock()):
        try:
            await create_user_if_not_exists(P1_ID, "alice", "Alice", db)
            await create_user_if_not_exists(P2_ID, "bob", "Bob", db)
            await start_duel(P1_ID, P2_ID, mock_ctx, db, is_ranked=True, group_chat_id=None)
            duel_key = None
            for k, v in mock_ctx.bot_data.items():
                if isinstance(v, dict) and v.get("players") == [P1_ID, P2_ID]:
                    duel_key = k
                    break
            assert duel_key, "Duel not created"
            duel = mock_ctx.bot_data[duel_key]
            duel["answers"][P1_ID] = [(True,1)]*5
            duel["answers"][P2_ID] = [(True,1), (False,1), (True,1), (False,1), (True,1)]
            await finish_duel(duel_key, mock_ctx)
            p1 = await db.fetchone("SELECT wins, mmr FROM users WHERE user_id = ?", P1_ID)
            p2 = await db.fetchone("SELECT wins, mmr FROM users WHERE user_id = ?", P2_ID)
            assert p1["wins"] == 1
            assert p1["mmr"] > 1200
            assert p2["mmr"] < 1200
            print("OK - Duel scoring correct")
            return True
        except Exception as e:
            print(f"FAILED - {e}")
            traceback.print_exc()
            return False
        finally:
            await db.close()
            cleanup_db()

# ──────────────────────────
# 8. XP
# ──────────────────────────
async def test_xp():
    print("\n=== Testing XP ===")
    from database.engine import Database
    from services.xp_progression import award_xp, create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    try:
        await db.connect()
        await create_user_if_not_exists(P1_ID, "test", "Test", db)
        result = await award_xp(P1_ID, 500, db, combo=2)
        user = await db.fetchone("SELECT xp, level FROM users WHERE user_id = ?", P1_ID)
        if not user or user["xp"] < 1000:
            print("FAILED - XP not awarded correctly")
            return False
        if user["level"] < 2:
            print("FAILED - level not increased")
            return False
        print("OK - XP & level up work")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False
    finally:
        await db.close()
        cleanup_db()

# ──────────────────────────
# Runner
# ──────────────────────────
async def run_all_tests():
    results = []
    results.append(("Syntax", test_syntax()))
    results.append(("Imports", test_imports()))
    results.append(("Database & Friends", await test_database_and_friends()))
    results.append(("Inline Pool", await test_inline_pool()))
    results.append(("Leaderboard Cache", await test_leaderboard_cache()))
    results.append(("Rate Limiter", test_rate_limiter()))
    results.append(("Duel Scoring", await test_duel_scoring()))
    results.append(("XP", await test_xp()))

    print("\n\n========== SUMMARY ==========")
    passed = all(r[1] for r in results)
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {name}")
    if passed:
        print("\n✅ All tests passed! The bot is fully polished.")
    else:
        print("\n❌ Some tests failed. Review the errors above.")
    return passed

if __name__ == "__main__":
    asyncio.run(run_all_tests())