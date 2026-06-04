from telegram import Update
from telegram.ext import ContextTypes

async def smart_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text, **kwargs):
    """Reply to either a message or a callback query."""
    if update.callback_query:
        await update.callback_query.edit_message_text(text, **kwargs)
    else:
        await update.message.reply_text(text, **kwargs)