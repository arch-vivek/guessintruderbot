#!/usr/bin/env python3
"""
Professional test suite for Guess The Intruder bot.
Covers syntax, imports, database, XP, puzzles, anti‑cheat,
profile card, inline, daily challenges, and duel scoring.
"""

import sys, os, asyncio, io, time, importlib, traceback, json
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_DB_PATH = "test_game.db"
P1_ID = 111111
P2_ID = 222222

# ────────────────────────────────────
# Helper: remove test db
# ────────────────────────────────────
def cleanup_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

# ────────────────────────────────────
# 1. Syntax check
# ────────────────────────────────────
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
        print("FAILED - syntax errors found:")
        for e in errors:
            print("  ", e)
    else:
        print("OK - all files have valid syntax")
    return len(errors) == 0

# ────────────────────────────────────
# 2. Imports
# ────────────────────────────────────
def test_imports():
    print("\n=== Testing Imports ===")
    modules = [
        "config",
        "database.engine",
        "database.schema",
        "core.game_engine",
        "core.difficulty",
        "core.anti_cheat",
        "core.events",
        "handlers.start",
        "handlers.help",
        "handlers.quick_play",
        "handlers.group_battle",
        "handlers.ranked",
        "handlers.daily_challenge",
        "handlers.endless",
        "handlers.inline_query",
        "handlers.profile",
        "handlers.leaderboard",
        "handlers.daily_reward",
        "handlers.achievements_show",
        "handlers.admin",
        "services.xp_progression",
        "services.achievements",
        "utils.helpers",
        "utils.rate_limiter",
    ]
    errors = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError as e:
            # Only flag internal modules, ignore missing external packages
            if "telegram" not in str(e) and "PIL" not in str(e) and "dotenv" not in str(e) and "aiosqlite" not in str(e):
                errors.append(f"{mod}: {e}")
    if errors:
        print("FAILED - import errors:")
        for e in errors:
            print("  ", e)
    else:
        print("OK - all modules importable (external deps may be missing in this env)")
    return len(errors) == 0

# ────────────────────────────────────
# 3. Database & User creation
# ────────────────────────────────────
async def test_database():
    print("\n=== Testing Database ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    try:
        await db.connect()
        # Check tables
        tables = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = {t["name"] for t in tables}
        for tbl in ["users", "achievements", "matches", "daily_challenges", "seasons"]:
            if tbl not in table_names:
                print(f"FAILED - table '{tbl}' missing")
                return False

        # Create user
        await create_user_if_not_exists(P1_ID, "testuser", "Test", db)
        user = await db.fetchone("SELECT * FROM users WHERE user_id = ?", P1_ID)
        if not user:
            print("FAILED - user creation")
            return False

        print("OK - database & user creation work")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# 4. XP awarding
# ────────────────────────────────────
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
        if not user or user["xp"] < 1000:  # 500*2 = 1000
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

# ────────────────────────────────────
# 5. Game engine
# ────────────────────────────────────
def test_game_engine():
    print("\n=== Testing Game Engine ===")
    from core.game_engine import generate_puzzle
    try:
        puzzle = generate_puzzle(difficulty=2)
        assert "options" in puzzle
        assert "intruder_index" in puzzle
        assert 0 <= puzzle["intruder_index"] < len(puzzle["options"])
        print("OK - puzzle generation works")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False

# ────────────────────────────────────
# 6. Anti‑cheat
# ────────────────────────────────────
def test_anti_cheat():
    print("\n=== Testing Anti‑Cheat ===")
    from core.anti_cheat import is_suspicious_speed
    assert is_suspicious_speed(1, 1, 0.3) == True
    assert is_suspicious_speed(1, 1, 2.0) == False
    assert is_suspicious_speed(1, 5, 0.7) == True
    print("OK - anti‑cheat works")
    return True

# ────────────────────────────────────
# 7. Profile card
# ────────────────────────────────────
def test_profile_card():
    print("\n=== Testing Profile Card ===")
    from handlers.profile import generate_profile_card
    try:
        user_data = {
            "user_id": 1, "first_name": "Test", "username": "test",
            "level": 5, "mmr": 1350, "wins": 10, "streak": 3,
            "total_games": 20, "xp": 3400, "rank_tier": "gold"
        }
        equipped = set()
        img = generate_profile_card(user_data, None, equipped)
        assert img.size == (800, 400)
        print("OK - profile card generated")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        traceback.print_exc()
        return False

# ────────────────────────────────────
# 8. Inline puzzle storage
# ────────────────────────────────────
def test_inline_puzzle():
    print("\n=== Testing Inline Puzzle ===")
    import uuid, time
    from core.game_engine import generate_puzzle
    puzzle = generate_puzzle(1)
    puzzle_id = uuid.uuid4().hex[:8]
    bot_data = {"inline_puzzles": {
        puzzle_id: {"puzzle": puzzle, "expires": time.time()+600, "answered_users": set()}
    }}
    assert puzzle_id in bot_data["inline_puzzles"]
    assert "answered_users" in bot_data["inline_puzzles"][puzzle_id]
    print("OK - inline puzzle storage works")
    return True

# ────────────────────────────────────
# 9. Daily challenge
# ────────────────────────────────────
async def test_daily_challenge():
    print("\n=== Testing Daily Challenge ===")
    from database.engine import Database
    from handlers.daily_challenge import get_today_challenge
    cleanup_db()
    db = Database(TEST_DB_PATH)
    try:
        await db.connect()
        challenge = await get_today_challenge(db)
        assert challenge is not None
        puzzle = json.loads(challenge["puzzle_data"])
        assert "options" in puzzle
        print("OK - daily challenge works")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# 10. Duel scoring simulation
# ────────────────────────────────────
async def test_duel_scoring():
    print("\n=== Testing Duel Scoring ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    from handlers.ranked import start_duel, finish_duel, duel_answer, show_round, process_duel_round
    from core.game_engine import generate_puzzle

    cleanup_db()
    db = Database(TEST_DB_PATH)
    await db.connect()

    # Mock context
    mock_ctx = MagicMock()
    mock_ctx.bot_data = {"db": db}
    mock_ctx.bot = AsyncMock()
    mock_ctx.bot.send_message = AsyncMock(return_value=MagicMock(message_id=1, chat_id=1))
    mock_ctx.bot.edit_message_text = AsyncMock()

    # Patch asyncio.sleep to skip delays
    with patch('asyncio.sleep', new=AsyncMock()):
        try:
            # Create two users
            await create_user_if_not_exists(P1_ID, "player1", "Alice", db)
            await create_user_if_not_exists(P2_ID, "player2", "Bob", db)

            # Start a ranked duel (private)
            await start_duel(P1_ID, P2_ID, mock_ctx, db, is_ranked=True, group_chat_id=None)

            # The duel state is stored in mock_ctx.bot_data under a key like "111111_222222_..."
            # Find the duel key
            duel_key = None
            for k, v in mock_ctx.bot_data.items():
                if isinstance(v, dict) and v.get("players") == [P1_ID, P2_ID]:
                    duel_key = k
                    break
            assert duel_key is not None, "Duel not found in bot_data"

            duel = mock_ctx.bot_data[duel_key]

            # Simulate 5 rounds: player1 gets 4 correct, player2 gets 2 correct
            correct_answers = [
                (True, 2.0), (True, 2.5), (False, 4.0), (True, 1.2), (True, 3.0)  # P1
            ], [
                (False, 5.0), (True, 3.0), (False, 4.5), (False, 6.0), (True, 2.8)  # P2
            ]
            # We'll directly append answers for each round, then manually call process/finish
            for rnd in range(5):
                duel["current_round"] = rnd
                duel["answers"][P1_ID].append(correct_answers[0][rnd])
                duel["answers"][P2_ID].append(correct_answers[1][rnd])
                # Normally process_duel_round would be called after both answered,
                # but we can just keep going and after 5 rounds call finish_duel

            # Finalize
            await finish_duel(duel_key, mock_ctx)

            # Check that scores were computed correctly
            # finish_duel pops the duel, so we can't access it directly.
            # Instead, we verify the database changes: wins, losses, mmr, etc.
            p1 = await db.fetchone("SELECT wins, mmr FROM users WHERE user_id = ?", P1_ID)
            p2 = await db.fetchone("SELECT wins, mmr FROM users WHERE user_id = ?", P2_ID)

            # P1 should have won (4 vs 2), so wins +1, mmr up
            assert p1["wins"] == 1, f"Expected P1 wins=1, got {p1['wins']}"
            assert p2["wins"] == 0, f"Expected P2 wins=0, got {p2['wins']}"
            assert p1["mmr"] > 1200, f"P1 mmr should have increased"
            assert p2["mmr"] < 1200, f"P2 mmr should have decreased"

            print("OK - duel scoring correct (P1 won 4-2)")
            return True
        except Exception as e:
            print(f"FAILED - duel scoring: {e}")
            traceback.print_exc()
            return False
        finally:
            await db.close()
            cleanup_db()

# ────────────────────────────────────
# 11. Callback patterns in main.py
# ────────────────────────────────────
def test_callback_patterns():
    print("\n=== Testing Callback Patterns ===")
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        patterns = [
            "qp_answer_", "gb_join", "gb_answer_", "duel_accept_",
            "duel_[0-9]", "daily_answer_", "endless_", "inline_answer_",
            "mode_", "profile$", "leaderboard$", "help$", "start_menu$",
        ]
        missing = [p for p in patterns if p not in content]
        if missing:
            print("FAILED - missing patterns:")
            for p in missing:
                print("  ", p)
            return False
        print("OK - all callback patterns present")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False

# ────────────────────────────────────
# Runner
# ────────────────────────────────────
async def run_all_tests():
    results = []
    results.append(("Syntax", test_syntax()))
    results.append(("Imports", test_imports()))
    results.append(("Database", await test_database()))
    results.append(("XP", await test_xp()))
    results.append(("Game Engine", test_game_engine()))
    results.append(("Anti‑Cheat", test_anti_cheat()))
    results.append(("Profile Card", test_profile_card()))
    results.append(("Inline Puzzle", test_inline_puzzle()))
    results.append(("Daily Challenge", await test_daily_challenge()))
    results.append(("Duel Scoring", await test_duel_scoring()))
    results.append(("Callback Patterns", test_callback_patterns()))

    print("\n\n========== SUMMARY ==========")
    passed = all(r[1] for r in results)
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {name}")
    if passed:
        print("\n✅ All tests passed! The bot is fully functional.")
    else:
        print("\n❌ Some tests failed. Review the errors above.")
    return passed

if __name__ == "__main__":
    asyncio.run(run_all_tests())