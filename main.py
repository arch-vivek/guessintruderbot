import asyncio, logging, time
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes, MessageHandler, filters
from telegram import Update
from telegram.error import NetworkError
from config import BOT_TOKEN
from database.engine import Database
from handlers.start import start, menu_redirect
from handlers.help import help_command
from handlers.quick_play import start_quick_play, handle_answer as qp_handle_answer
from handlers.group_battle import (
    group_battle_command, join_battle, handle_join_callback, gb_answer_callback
)
from handlers.ranked import ranked_start, duel_answer, duel_command, duel_accept_callback
from handlers.daily_challenge import start_daily, daily_answer
from handlers.endless import start_endless, endless_answer
from handlers.inline_query import inline_query, inline_answer_callback
from handlers.profile import profile_command
from handlers.leaderboard import leaderboard_global
from handlers.daily_reward import daily_reward_command
from handlers.achievements_show import achievements_command
from handlers.friends import add_friend, accept_friend, list_friends, friend_duel
from handlers.free_chat import free_chat_reply
from handlers.admin import admin_broadcast, admin_give, admin_setprofile, admin_info
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import core.events as events

# Hide token from logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Global scheduler
scheduler = AsyncIOScheduler()

_last_net_error_ts = 0

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    global _last_net_error_ts
    exc = context.error

    if isinstance(exc, NetworkError):
        now = time.monotonic()
        if now - _last_net_error_ts < 60:
            return
        _last_net_error_ts = now
        logging.getLogger(__name__).warning(
            "Network error – bot will retry automatically. Check your internet connection."
        )
        await asyncio.sleep(5)
        return

    logging.getLogger(__name__).error(msg="Exception while handling an update:", exc_info=exc)
    if update and hasattr(update, 'effective_chat'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ An internal error occurred. Please try again later."
            )
        except Exception:
            pass

async def post_init(app):
    db = Database()
    await db.connect()
    app.bot_data["db"] = db
    app.bot_data["gb_lobbies"] = {}
    app.bot_data["gb_rounds"] = {}
    app.bot_data["double_xp"] = False

    scheduler.start()
    scheduler.add_job(
        lambda: setattr(events, 'DOUBLE_XP', True),
        'interval', hours=4, next_run_time=datetime.now()+timedelta(minutes=30)
    )
    scheduler.add_job(
        lambda: setattr(events, 'DOUBLE_XP', False),
        'interval', hours=4, next_run_time=datetime.now()+timedelta(minutes=60)
    )

    async def cleanup_inline():
        inline_puzzles = app.bot_data.get("inline_puzzles", {})
        now = time.time()
        expired = [pid for pid, data in inline_puzzles.items() if data.get("expires", 0) < now]
        for pid in expired:
            del inline_puzzles[pid]
    scheduler.add_job(cleanup_inline, 'interval', minutes=5)

    from core.game_engine import generate_puzzle
    import random, asyncio
    async def warm_pool():
        while True:
            puzzles = [generate_puzzle(difficulty=random.randint(1,2)) for _ in range(15)]
            app.bot_data["inline_pool"] = puzzles
            await asyncio.sleep(180)   # refresh every 3 minutes
    asyncio.create_task(warm_pool())

    async def cache_leaderboard(app):
        while True:
            db = app.bot_data["db"]
            top = await db.fetchall("SELECT user_id, username, first_name, level, mmr FROM users ORDER BY mmr DESC LIMIT 20")
            app.bot_data["leaderboard_cache"] = top
            await asyncio.sleep(30)
    asyncio.create_task(cache_leaderboard(app))

async def post_shutdown(app):
    db = app.bot_data.get("db")
    if db:
        await db.close()
    try:
        scheduler.shutdown()
    except Exception:
        pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    # Commands (with aliases)
    app.add_handler(CommandHandler(["start"], start))
    app.add_handler(CommandHandler(["help", "h"], help_command))
    app.add_handler(CommandHandler(["profile", "p"], profile_command))
    app.add_handler(CommandHandler(["leaderboard", "l", "top"], leaderboard_global))
    app.add_handler(CommandHandler(["battle", "b"], group_battle_command))
    app.add_handler(CommandHandler(["join", "j"], join_battle))
    app.add_handler(CommandHandler(["ranked", "r"], ranked_start))
    app.add_handler(CommandHandler(["duel", "challenge"], duel_command))
    app.add_handler(CommandHandler(["daily", "d"], start_daily))
    app.add_handler(CommandHandler(["endless", "e"], start_endless))
    app.add_handler(CommandHandler(["reward", "bonus"], daily_reward_command))
    app.add_handler(CommandHandler(["achievements", "ach"], achievements_command))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    app.add_handler(CommandHandler("admin_give", admin_give))
    app.add_handler(CommandHandler("admin_setprofile", admin_setprofile))
    app.add_handler(CommandHandler("admin_info", admin_info))
    app.add_handler(CommandHandler("addfriend", add_friend))
    app.add_handler(CommandHandler("acceptfriend", accept_friend))
    app.add_handler(CommandHandler("friends", list_friends))
    app.add_handler(CommandHandler("friendduel", friend_duel))

    # Callback Handlers – order matters!
    app.add_handler(CallbackQueryHandler(qp_handle_answer, pattern="^qp_answer_"))
    app.add_handler(CallbackQueryHandler(handle_join_callback, pattern="^gb_join"))
    app.add_handler(CallbackQueryHandler(gb_answer_callback, pattern="^gb_answer_"))
    # Accept duel buttons MUST come before general duel handler
    app.add_handler(CallbackQueryHandler(duel_accept_callback, pattern="^duel_accept_"))
    app.add_handler(CallbackQueryHandler(duel_answer, pattern="^duel_[0-9]"))
    app.add_handler(CallbackQueryHandler(daily_answer, pattern="^daily_answer_"))
    app.add_handler(CallbackQueryHandler(endless_answer, pattern="^endless_"))
    app.add_handler(CallbackQueryHandler(inline_answer_callback, pattern="^inline_answer_"))
    app.add_handler(CallbackQueryHandler(menu_redirect, pattern="^mode_|^profile$|^shop$|^leaderboard$|^help$|^start_menu$"))
        # Free chatbot replies in private chat (rate‑limited)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, free_chat_reply))
    
    # Inline challenge friend
    async def challenge_general(update, context):
        try:
            await update.callback_query.answer("Duel feature coming soon! Use /ranked to queue.", show_alert=True)
        except:
            pass
    app.add_handler(CallbackQueryHandler(challenge_general, pattern="^challenge_general$"))

    # Inline queries
    app.add_handler(InlineQueryHandler(inline_query))

    # Track groups: when bot is added to a group
    async def on_bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat.type in ("group", "supergroup"):
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    db = context.bot_data["db"]
                    await db.execute(
                        "INSERT OR IGNORE INTO bot_chats (chat_id, type) VALUES (?, ?)",
                        chat.id, chat.type
                    )
                    break
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added))

    # Track groups: any message in a group records the group
    async def record_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat.type in ("group", "supergroup"):
            db = context.bot_data["db"]
            await db.execute(
                "INSERT OR IGNORE INTO bot_chats (chat_id, type) VALUES (?, ?)",
                chat.id, chat.type
            )
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, record_group_message))

    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()