from telegram import Update
from telegram.ext import ContextTypes

async def track_new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record any group/supergroup the bot is added to."""
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        db = context.bot_data["db"]
        await db.execute(
            "INSERT OR IGNORE INTO bot_chats (chat_id, type) VALUES (?, ?)",
            chat.id, chat.type
        )

async def track_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fired when the bot's own chat member status changes (added/removed)."""
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        db = context.bot_data["db"]
        new_status = update.my_chat_member.new_chat_member.status
        if new_status in ("member", "administrator"):
            await db.execute(
                "INSERT OR IGNORE INTO bot_chats (chat_id, type) VALUES (?, ?)",
                chat.id, chat.type
            )
        elif new_status in ("left", "kicked"):
            await db.execute(
                "DELETE FROM bot_chats WHERE chat_id = ?",
                chat.id
            )