import asyncio, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.game_engine import generate_puzzle
from services.xp_progression import award_xp
from utils.helpers import smart_reply

async def start_endless(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user = update.effective_user
    db = context.bot_data["db"]

    context.user_data["endless"] = {
        "round": 0,
        "score": 0,
        "combo": 0,
        "active": True,
        "chat_id": update.effective_chat.id
    }

    # If called from command, send a new message; if callback, edit the existing one.
    if query:
        await query.answer()
        await send_endless_round(query.message, context, is_callback=True)
    else:
        msg = await update.message.reply_text("Starting endless mode...")
        await send_endless_round(msg, context, is_callback=False)

async def send_endless_round(message, context, is_callback=True):
    if not context.user_data["endless"]["active"]:
        return
    difficulty = min(1 + context.user_data["endless"]["round"] // 3, 5)
    puzzle = generate_puzzle(difficulty)
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"endless_{i}")] for i, opt in enumerate(puzzle["options"])]

    text = f"♾️ *Endless Mode* — Round {context.user_data['endless']['round']+1}\n\n" + "\n".join(puzzle["options"])
    if is_callback:
        msg = await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        msg = await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    context.user_data["endless"]["puzzle"] = puzzle
    context.user_data["endless"]["start_time"] = time.monotonic()
    context.user_data["endless"]["message_id"] = msg.message_id

async def endless_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = context.user_data.get("endless")
    if not data or not data.get("active"):
        await query.answer("No game.", show_alert=True)
        return
    chosen_idx = int(query.data.split("_")[1])
    puzzle = data["puzzle"]
    correct = (chosen_idx == puzzle["intruder_index"])
    elapsed = time.monotonic() - data["start_time"]
    db = context.bot_data["db"]

    if correct:
        data["round"] += 1
        data["combo"] += 1
        data["score"] += 100 + max(0, int(50 - elapsed * 5))
        await award_xp(user.id, 20, db, combo=data["combo"])
        await query.answer(f"✅ +{data['score']} pts")
        await send_endless_round(query.message, context, is_callback=True)
    else:
        data["active"] = False
        await query.edit_message_text(
            f"💀 *Game Over*\n\nRounds survived: {data['round']}\nScore: {data['score']}\nMax Combo: {data['combo']}\n\nWrong! The intruder was {puzzle['options'][puzzle['intruder_index']]}",
            parse_mode="Markdown"
        )