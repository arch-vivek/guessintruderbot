import random
from telegram import Update
from telegram.ext import ContextTypes
from utils.rate_limiter import RateLimiter

chat_limiter = RateLimiter(max_calls=5, period=60)

FAQ = {
    # ---------- General ----------
    "how to play": (
        "🤖 *How to Play Guess The Intruder*\n\n"
        "You'll see a set of emojis/words – one of them *does not belong* to the same category as the others. "
        "Tap the intruder before time runs out! The faster you answer, the more XP you get.\n\n"
        "Try a game now: /start → ⚡ Quick Play.\n"
        "Full guide: /help"
    ),
    "rules": (
        "🤖 *Game Rules*\n\n"
        "• Each puzzle has 4‑6 items, one is the intruder.\n"
        "• Quick Play: 10 seconds to answer, combo multiplier up to x10.\n"
        "• Group Battle: 5 elimination rounds, last survivor wins.\n"
        "• Ranked: 5‑round duel, winner gains MMR, loser loses MMR.\n"
        "• Daily Challenge: one puzzle per day, bonus XP on correct.\n"
        "• Endless: survive as long as you can, difficulty scales up."
    ),
    "what is this": (
        "🤖 *Guess The Intruder* is a Telegram‑native multiplayer puzzle game. "
        "Find the odd one out from a group of emojis/words. Play solo, with friends, or compete globally.\n\n"
        "Get started: /start"
    ),

    # ---------- Modes ----------
    "quick play": (
        "⚡ *Quick Play*\n\n"
        "Fast solo rounds. Each round lasts 10 seconds. The more correct answers you chain, the higher your combo – up to x10 XP! "
        "Use it to warm up or climb the levels.\n"
        "Start: /start → ⚡ Quick Play"
    ),
    "group battle": (
        "👥 *Group Battle*\n\n"
        "Play with friends or strangers in a Telegram group.\n"
        "1. Start a lobby with /battle\n"
        "2. Others join with /join (or tap Join button)\n"
        "3. After 30s, 5 elimination rounds begin. Wrong answer = you're out.\n"
        "Last survivor wins! Great for parties and communities."
    ),
    "ranked": (
        "🏆 *Ranked Duels*\n\n"
        "Competitive matchmaking based on MMR (matchmaking rating).\n"
        "Join the global queue with /ranked. The system pairs you with an opponent of similar skill.\n"
        "A 5‑round duel is played in private. Winner gains MMR, loser loses MMR.\n"
        "Leagues: Bronze → Silver → Gold → Platinum → Diamond → Master → Mythic."
    ),
    "duel": (
        "🤺 *Duels*\n\n"
        "Direct challenge to a friend (casual, no MMR change) or random opponent (ranked).\n"
        "• Casual duel: reply to a friend's message with /duel, or use /duel @username. The challenge appears in the chat.\n"
        "• Ranked: type /ranked to enter the global queue.\n"
        "Both types are 5 rounds, and you get XP regardless of the outcome."
    ),
    "daily challenge": (
        "📅 *Daily Challenge*\n\n"
        "A unique puzzle every day. You get only one attempt. If you answer correctly, you earn 150 XP.\n"
        "Use /daily to play. Come back each day for a new challenge!"
    ),
    "endless": (
        "♾️ *Endless Mode*\n\n"
        "Survival mode – rounds keep coming until you make a mistake. Difficulty increases every few rounds.\n"
        "Aim for a high score and a long combo! Start with /endless."
    ),

    # ---------- Progression ----------
    "achievements": (
        "🏅 *Achievements*\n\n"
        "Unlock badges by reaching milestones. Examples:\n"
        "• First Victory – win your first game\n"
        "• Hot Streak – 5 consecutive wins\n"
        "• Level 10 / Level 50 – reach those levels\n"
        "• Perfect Round – answer in under 2 seconds\n\n"
        "View your progress: /achievements"
    ),
    "xp": (
        "💠 *Experience Points (XP)*\n\n"
        "Earn XP by playing any mode. Higher combos, streaks, and faster answers give more XP. "
        "Level up to unlock achievements and climb the leaderboard.\n"
        "Check your XP: /profile"
    ),
    "level": (
        "⬆️ *Levels*\n\n"
        "Your level increases as you earn XP. Each level requires more XP (100 × level²). "
        "Leveling up can trigger achievement unlocks. See your level with /profile."
    ),
    "mmr": (
        "📊 *MMR (Matchmaking Rating)*\n\n"
        "A number that represents your competitive skill. Starts at 1200. Goes up with ranked wins, down with losses.\n"
        "Your MMR determines your rank (Bronze to Mythic). View it on /profile or /leaderboard."
    ),
    "streak": (
        "🔥 *Streak*\n\n"
        "Consecutive correct answers in Quick Play. The longer your streak, the higher your combo multiplier (up to x10).\n"
        "Every 5‑streak milestone gives bonus XP. Streak is displayed on your profile card."
    ),
    "reward": (
        "🎁 *Daily Reward*\n\n"
        "Claim free XP every day with /reward. The amount increases with your daily streak (logging in on consecutive days).\n"
        "A 7‑day streak gives a special bonus! Don't miss a day."
    ),
    "daily reward": (
        "🎁 *Daily Reward*\n\n"
        "Claim free XP every day with /reward. The amount increases with your daily streak (logging in on consecutive days).\n"
        "A 7‑day streak gives a special bonus! Don't miss a day."
    ),
    "bonus": (
        "🎁 *Daily Reward*\n\n"
        "Claim free XP every day with /reward. The amount increases with your daily streak (logging in on consecutive days).\n"
        "A 7‑day streak gives a special bonus! Don't miss a day."
    ),

    # ---------- Social ----------
    "friend": (
        "👥 *Friends System*\n\n"
        "Add other players as friends and see their stats. Commands:\n"
        "• /addfriend @username – send request\n"
        "• /acceptfriend @username – accept a request\n"
        "• /friends – list your friends\n"
        "• /friendduel @username – start a casual duel with a friend\n"
        "Friends make the game more fun!"
    ),
    "add friend": (
        "👥 *Friends System*\n\n"
        "Add other players as friends and see their stats. Commands:\n"
        "• /addfriend @username – send request\n"
        "• /acceptfriend @username – accept a request\n"
        "• /friends – list your friends\n"
        "• /friendduel @username – start a casual duel with a friend\n"
        "Friends make the game more fun!"
    ),
    "friend duel": (
        "🤺 *Friend Duel*\n\n"
        "Start a casual duel with a friend (no MMR change). Use /friendduel @username. Both players receive private messages with 5 rounds.\n"
        "Works only if you are already friends."
    ),

    # ---------- Profile & Stats ----------
    "profile": (
        "👤 *Profile Card*\n\n"
        "A beautiful, old‑money style card showing your level, MMR, wins, streak, and XP progress. "
        "It also displays your Telegram profile picture.\n"
        "View with /profile or /p."
    ),
    "leaderboard": (
        "🏅 *Leaderboard*\n\n"
        "Top 10 players by MMR worldwide. Updated in real time.\n"
        "Check it with /leaderboard, /l, or /top."
    ),
    "stats": (
        "📈 *Your Stats*\n\n"
        "See your wins, losses, total games, level, MMR, streak, and more on your profile card.\n"
        "Use /profile to view them."
    ),

    # ---------- Help ----------
    "help": (
        "ℹ️ *Help Menu*\n\n"
        "All commands and game modes are explained under /help. You can also tap any button in the main menu to learn more.\n"
        "If you have a specific question, just ask me!"
    ),
}

FALLBACK = [
    "Hey there! 👋 Ready for a round of Guess The Intruder?",
    "Hello! 😊 Want to check your stats? Try /profile.",
    "Hi! 🌟 Feeling competitive? Queue for /ranked!",
    "Hey hey! 🎮 Let's play a quick game – tap /start!",
    "Hello, friend! 🤗 Did you claim your daily /reward?",
    "Hi! 💬 I'm here if you have any questions about the game.",
    "Hey! 🚀 Let's find some intruders!",
    "Hi there! 🔥 Your next big streak is waiting.",
    "Hello! 🧠 Did you know? Practice makes perfect in /daily.",
    "Hey! 🎯 Challenge a friend with /duel!",
    "Hi! 🏆 Check your profile with /profile.",
    "Hello! 💡 Stuck on a puzzle? The intruder is always watching.",
    "Hey! ⚡ Quick Play is great for warming up.",
    "Hi! 🌈 Every master was once a beginner.",
    "Hello! 🎲 Life is like a puzzle – sometimes the odd one out is you.",
    "Hey! 🪄 I believe in you!",
    "Hi! 📈 Your MMR is waiting to climb.",
    "Hello! 🎪 Join the fun – /battle in a group!",
    "Hey! 🗺️ Explore all modes – there's so much to do.",
    "Hi! 🧩 Keep your mind sharp with /daily challenge.",
]

async def free_chat_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if msg.chat.type != "private":
        return
    if msg.text and msg.text.startswith("/"):
        return
    if not await chat_limiter.is_allowed(user.id):
        return

    text_lower = msg.text.strip().lower()
    reply = None

    # Search for keyword matches
    for keyword, answer in FAQ.items():
        if keyword in text_lower:
            reply = answer
            break

    if reply is None:
        reply = random.choice(FALLBACK)

    await msg.reply_text(reply, parse_mode="Markdown")