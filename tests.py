#!/usr/bin/env python3
"""
Comprehensive test suite for Guess The Intruder bot.
Tests all features: back buttons, inline play again, rate limits,
friend system, broadcast, group tracking, duel scoring, etc.
Run with: python tests.py  (inside your venv)
"""

import sys, os, asyncio, time, importlib, traceback, json
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_DB_PATH = "test_game.db"
P1_ID = 111111
P2_ID = 222222
ADMIN_ID = 999999

def cleanup_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

# ────────────────────────────────────
# Helper to create a mock update and context
# ────────────────────────────────────
class MockContext:
    def __init__(self, bot_data=None, user_data=None, args=None):
        self.bot_data = bot_data or {}
        self.user_data = user_data or {}
        self.args = args or []
        self.bot = AsyncMock()
        self.bot.send_message = AsyncMock(return_value=MagicMock(message_id=1, chat_id=1))
        self.bot.edit_message_text = AsyncMock()
        self.bot.get_user_profile_photos = AsyncMock()
        self.bot.get_user_profile_photos.return_value = MagicMock(total_count=0)

def make_callback_update(user, data, message=None, chat_id=1):
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.from_user = user
    update.callback_query.data = data
    # Make the message object with async reply methods
    msg = MagicMock()
    msg.reply_photo = AsyncMock()
    msg.reply_text = AsyncMock()
    msg.chat_id = chat_id
    msg.message_id = 10
    msg.text = "dummy"
    update.callback_query.message = msg
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.edit_message_reply_markup = AsyncMock()
    update.message = None
    update.effective_user = user
    update.effective_chat = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_chat.type = "private"
    return update

def make_message_update(user, text, chat_id=1, is_group=False):
    update = MagicMock()
    msg = MagicMock()
    msg.from_user = user
    msg.text = text
    msg.chat_id = chat_id
    msg.chat = MagicMock()
    msg.chat.type = "group" if is_group else "private"
    msg.reply_text = AsyncMock()
    msg.reply_photo = AsyncMock()
    msg.reply_to_message = None
    update.message = msg
    update.callback_query = None
    update.effective_user = user
    update.effective_chat = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_chat.type = "group" if is_group else "private"
    return update

def make_user(id, username, first_name):
    user = MagicMock()
    user.id = id
    user.username = username
    user.first_name = first_name
    return user

# ────────────────────────────────────
# 1. Syntax
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
        print("FAILED")
        for e in errors:
            print("  ", e)
    else:
        print("OK")
    return len(errors) == 0

# ────────────────────────────────────
# 2. Imports
# ────────────────────────────────────
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
            if "telegram" not in str(e) and "PIL" not in str(e) and "dotenv" not in str(e) and "aiosqlite" not in str(e):
                errors.append(f"{mod}: {e}")
    if errors:
        print("FAILED")
        for e in errors:
            print("  ", e)
    else:
        print("OK")
    return len(errors) == 0

# ────────────────────────────────────
# 3. Database setup
# ────────────────────────────────────
async def test_database():
    print("\n=== Testing Database ===")
    from database.engine import Database
    cleanup_db()
    db = Database(TEST_DB_PATH)
    try:
        await db.connect()
        tables = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = {t["name"] for t in tables}
        required = ["users", "friendships", "achievements", "matches", "daily_challenges", "seasons", "bot_chats"]
        for tbl in required:
            if tbl not in table_names:
                print(f"FAILED - table '{tbl}' missing")
                return False
        print("OK")
        return True
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# 4. Back buttons in various handlers
# ────────────────────────────────────
async def test_back_buttons():
    print("\n=== Testing Back Buttons ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    await db.connect()
    try:
        await create_user_if_not_exists(P1_ID, "testuser", "Test", db)
        user = make_user(P1_ID, "testuser", "Test")

        # Test Profile
        context = MockContext(bot_data={"db": db})
        update = make_callback_update(user, "profile")
        from handlers.profile import profile_command
        await profile_command(update, context)
        # The profile_command sends a photo and then a text with back button.
        # Check that reply_photo was called
        assert update.callback_query.message.reply_photo.called, "Profile photo not sent"
        # Check that a "Return to menu" message was sent via send_message or reply_text
        # In our profile handler, we use update.callback_query.message.reply_text for back button.
        reply_text_calls = update.callback_query.message.reply_text.call_args_list
        found_back = any("Return to menu" in str(args) for args in reply_text_calls)
        assert found_back, "Profile back button missing"

        # Test Leaderboard
        update = make_callback_update(user, "leaderboard")
        from handlers.leaderboard import leaderboard_global
        await leaderboard_global(update, context)
        edit_calls = update.callback_query.edit_message_text.call_args_list
        found_back = any("Back to Menu" in str(args) for args in edit_calls)
        assert found_back, "Leaderboard back button missing"

        # Test Help
        update = make_callback_update(user, "help")
        from handlers.help import help_command
        await help_command(update, context)
        edit_calls = update.callback_query.edit_message_text.call_args_list
        found_back = any("Back to Menu" in str(args) for args in edit_calls)
        assert found_back, "Help back button missing"

        print("OK")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        traceback.print_exc()
        return False
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# 5. Inline Play Again
# ────────────────────────────────────
async def test_inline_play_again():
    print("\n=== Testing Inline Play Again ===")
    from handlers.inline_query import inline_answer_callback, inline_play_again_callback
    from core.game_engine import generate_puzzle
    cleanup_db()
    from database.engine import Database
    db = Database(TEST_DB_PATH)
    await db.connect()
    try:
        user = make_user(P1_ID, "test", "Test")
        puzzle = generate_puzzle(1)
        puzzle_id = "test123"
        context = MockContext(bot_data={
            "db": db,
            "inline_puzzles": {
                puzzle_id: {"puzzle": puzzle, "expires": time.time()+600, "answered_users": set()}
            }
        })
        update = make_callback_update(user, f"inline_answer_{puzzle_id}_{puzzle['intruder_index']}")
        await inline_answer_callback(update, context)
        edit_calls = update.callback_query.edit_message_text.call_args_list
        found_play_again = any("Play Again" in str(args) for args in edit_calls)
        assert found_play_again, "Play Again button not added"

        # Simulate Play Again click
        update2 = make_callback_update(user, "inline_play_again")
        await inline_play_again_callback(update2, context)
        edit_calls2 = update2.callback_query.edit_message_text.call_args_list
        text = edit_calls2[-1].args[0] if edit_calls2 else ""
        assert "Guess the Intruder" in str(text), "Play Again didn't load new puzzle"

        print("OK")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        traceback.print_exc()
        return False
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# 6. Rate limiter
# ────────────────────────────────────
async def test_rate_limiter():
    print("\n=== Testing Rate Limiter ===")
    from utils.rate_limiter import RateLimiter
    limiter = RateLimiter(max_calls=3, period=2)
    assert await limiter.is_allowed(123) == True
    assert await limiter.is_allowed(123) == True
    assert await limiter.is_allowed(123) == True
    assert await limiter.is_allowed(123) == False
    await asyncio.sleep(2.1)
    assert await limiter.is_allowed(123) == True
    print("OK")
    return True

# ────────────────────────────────────
# 7. Duel scoring
# ────────────────────────────────────
async def test_duel_scoring():
    print("\n=== Testing Duel Scoring ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    from handlers.ranked import start_duel, finish_duel
    cleanup_db()
    db = Database(TEST_DB_PATH)
    await db.connect()
    mock_ctx = MockContext(bot_data={"db": db})
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
            print("OK")
            return True
        except Exception as e:
            print(f"FAILED - {e}")
            traceback.print_exc()
            return False
        finally:
            await db.close()
            cleanup_db()

# ────────────────────────────────────
# 8. Friend system
# ────────────────────────────────────
async def test_friend_system():
    print("\n=== Testing Friend System ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    await db.connect()
    try:
        await create_user_if_not_exists(P1_ID, "alice", "Alice", db)
        await create_user_if_not_exists(P2_ID, "bob", "Bob", db)
        from handlers.friends import add_friend, accept_friend, list_friends, friend_duel

        user_alice = make_user(P1_ID, "alice", "Alice")
        update = make_message_update(user_alice, "/addfriend bob")
        context = MockContext(bot_data={"db": db}, args=["bob"])
        await add_friend(update, context)
        req = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", P1_ID, P2_ID)
        assert req and req["status"] == "pending", "Friend request not created"

        user_bob = make_user(P2_ID, "bob", "Bob")
        update = make_message_update(user_bob, "/acceptfriend alice")
        context = MockContext(bot_data={"db": db}, args=["alice"])
        await accept_friend(update, context)
        f1 = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", P1_ID, P2_ID)
        f2 = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", P2_ID, P1_ID)
        assert f1 and f1["status"] == "accepted", "Friendship not accepted"
        assert f2 and f2["status"] == "accepted", "Bidirectional friendship missing"

        update = make_message_update(user_alice, "/friends")
        context = MockContext(bot_data={"db": db})
        await list_friends(update, context)
        sent_text = update.message.reply_text.call_args[0][0]
        assert "Bob" in sent_text, "Friend not listed"

        update = make_message_update(user_alice, "/friendduel bob")
        context = MockContext(bot_data={"db": db}, args=["bob"])
        await friend_duel(update, context)
        assert context.bot.send_message.call_count >= 2, "Friend duel not started"

        print("OK")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        traceback.print_exc()
        return False
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# 9. Broadcast groups
# ────────────────────────────────────
async def test_broadcast_groups():
    print("\n=== Testing Broadcast Groups ===")
    from database.engine import Database
    from services.xp_progression import create_user_if_not_exists
    cleanup_db()
    db = Database(TEST_DB_PATH)
    await db.connect()
    try:
        await create_user_if_not_exists(ADMIN_ID, "admin", "Admin", db)
        await db.execute("INSERT OR IGNORE INTO bot_chats (chat_id, type) VALUES (?, 'group')", -12345)

        from handlers.admin import admin_broadcast
        user_admin = make_user(ADMIN_ID, "admin", "Admin")
        update = make_message_update(user_admin, "/admin_broadcast Hello world")
        context = MockContext(bot_data={"db": db}, args=["Hello", "world"])

        import config
        original_ids = config.ADMIN_IDS
        config.ADMIN_IDS = [ADMIN_ID]
        await admin_broadcast(update, context)
        config.ADMIN_IDS = original_ids

        # Collect all chat_ids that received a message
        sent_chat_ids = []
        for call in context.bot.send_message.call_args_list:
            pos_args = call[0]
            if pos_args:
                sent_chat_ids.append(pos_args[0])

        # The admin user (ADMIN_ID) and the group (-12345) must both be present
        assert ADMIN_ID in sent_chat_ids, "Admin user did not receive broadcast"
        assert -12345 in sent_chat_ids, "Group did not receive broadcast"
        print("OK")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        traceback.print_exc()
        return False
    finally:
        await db.close()
        cleanup_db()
# 10. XP
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
        if not user or user["xp"] < 1000:
            print("FAILED - XP not awarded correctly")
            return False
        if user["level"] < 2:
            print("FAILED - level not increased")
            return False
        print("OK")
        return True
    except Exception as e:
        print(f"FAILED - {e}")
        return False
    finally:
        await db.close()
        cleanup_db()

# ────────────────────────────────────
# Runner
# ────────────────────────────────────
async def run_all_tests():
    results = []
    results.append(("Syntax", test_syntax()))
    results.append(("Imports", test_imports()))
    results.append(("Database", await test_database()))
    results.append(("Back Buttons", await test_back_buttons()))
    results.append(("Inline Play Again", await test_inline_play_again()))
    results.append(("Rate Limiter", await test_rate_limiter()))
    results.append(("Duel Scoring", await test_duel_scoring()))
    results.append(("Friend System", await test_friend_system()))
    results.append(("Broadcast Groups", await test_broadcast_groups()))
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