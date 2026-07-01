from telegram import Update
from telegram.ext import ContextTypes
from log import logger

async def add_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    db = context.bot_data["db"]
    if not context.args:
        await update.message.reply_text("Usage: /addfriend @username")
        return
    target_username = context.args[0].lstrip("@").lower()
    target = await db.fetchone("SELECT user_id FROM users WHERE LOWER(username) = ?", target_username)
    if not target:
        await update.message.reply_text("User not found. They must have started the bot.")
        return
    if target["user_id"] == sender.id:
        await update.message.reply_text("You can't add yourself.")
        return
    existing = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ?", sender.id, target["user_id"])
    if existing:
        if existing["status"] == "accepted":
            await update.message.reply_text("You are already friends.")
        else:
            await update.message.reply_text("Friend request already sent.")
        return
    await db.execute("INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'pending')", sender.id, target["user_id"])
    await update.message.reply_text(f"Friend request sent to @{target_username}!")
    logger.info(f"User {sender.id} added friend @{target_username}")

async def accept_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]
    if not context.args:
        await update.message.reply_text("Usage: /acceptfriend @username")
        return
    requester_username = context.args[0].lstrip("@").lower()
    requester = await db.fetchone("SELECT user_id FROM users WHERE LOWER(username) = ?", requester_username)
    if not requester:
        await update.message.reply_text("User not found.")
        return
    # Find pending request FROM requester TO current user
    row = await db.fetchone("SELECT * FROM friendships WHERE user_id = ? AND friend_id = ? AND status = 'pending'", requester["user_id"], user.id)
    if not row:
        await update.message.reply_text("No pending request from this user.")
        return
    await db.execute("UPDATE friendships SET status = 'accepted' WHERE user_id = ? AND friend_id = ?", requester["user_id"], user.id)
    # Make it bidirectional
    await db.execute("INSERT OR IGNORE INTO friendships (user_id, friend_id, status) VALUES (?, ?, 'accepted')", user.id, requester["user_id"])
    await update.message.reply_text(f"Now friends with @{requester_username}!")
    logger.info(f"User {user.id} accepted friend request from @{requester_username}")

async def list_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]
    friends = await db.fetchall("""
        SELECT u.user_id, u.username, u.first_name
        FROM friendships f
        JOIN users u ON u.user_id = f.friend_id
        WHERE f.user_id = ? AND f.status = 'accepted'
    """, user.id)
    if not friends:
        await update.message.reply_text("No friends yet.")
        return
    text = "👥 *Your Friends*\n\n"
    for f in friends:
        name = f["first_name"] or f["username"] or str(f["user_id"])
        text += f"• {name} (@{f['username']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def friend_duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a casual duel directly with a friend."""
    challenger = update.effective_user
    db = context.bot_data["db"]
    if not context.args:
        await update.message.reply_text("Usage: /friendduel @username")
        return
    target_username = context.args[0].lstrip("@").lower()
    target = await db.fetchone("SELECT user_id FROM users WHERE LOWER(username) = ?", target_username)
    if not target:
        await update.message.reply_text("Friend not found. Use /addfriend first.")
        return
    # Check friendship
    friendship = await db.fetchone("SELECT status FROM friendships WHERE user_id = ? AND friend_id = ? AND status = 'accepted'", challenger.id, target["user_id"])
    if not friendship:
        await update.message.reply_text("You are not friends yet.")
        return
    from handlers.ranked import start_duel
    # Start a casual duel (no MMR change)
    await start_duel(challenger.id, target["user_id"], context, db, is_ranked=False, group_chat_id=None)
    await update.message.reply_text(f"⚔️ Casual duel started with @{target_username}! Check your private messages.")
    