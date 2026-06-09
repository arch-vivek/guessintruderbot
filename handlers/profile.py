import io, os
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ContextTypes
from services.xp_progression import get_user, xp_for_level
from utils.helpers import smart_reply

FONT_PATH_BOLD = "assets/fonts/PlayfairDisplay-Bold.ttf"
FONT_PATH_REGULAR = "assets/fonts/PlayfairDisplay-Regular.ttf"

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data["db"]
    profile = await get_user(user.id, db)
    if not profile:
        await smart_reply(update, context, "Profile not found. Use /start first.")
        return

    # No equipped items – use empty set
    equipped_set = set()

    # Fetch user's profile photo
    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    photo_bytes = None
    if photos.total_count > 0:
        photo = photos.photos[0][-1]
        file = await context.bot.get_file(photo.file_id)
        bio = io.BytesIO()
        await file.download_to_memory(bio)
        photo_bytes = bio.getvalue()

    # Generate the card image
    card_img = generate_profile_card(profile, photo_bytes, equipped_set)

    # Save to BytesIO
    card_bio = io.BytesIO()
    card_img.save(card_bio, "PNG")
    card_bio.seek(0)

    # Send as photo – handle both callback and direct message
    if update.callback_query:
        await update.callback_query.message.reply_photo(photo=card_bio, caption="Your Profile")
        try:
            await update.callback_query.answer()
        except:
            pass
    else:
        await update.message.reply_photo(photo=card_bio, caption="Your Profile")

def generate_profile_card(user_data: dict, profile_photo_bytes: bytes | None, equipped_set: set) -> Image.Image:
    # Canvas 800x400 – warm cream background
    bg_color = (245, 240, 230)
    img = Image.new("RGBA", (800, 400), bg_color)
    draw = ImageDraw.Draw(img)

    # ---------- Font loading ----------
    try:
        if os.path.exists(FONT_PATH_BOLD):
            font_title = ImageFont.truetype(FONT_PATH_BOLD, 36)
            font_text = ImageFont.truetype(FONT_PATH_BOLD, 22)
            font_small = ImageFont.truetype(FONT_PATH_REGULAR, 16)
        else:
            font_title = ImageFont.truetype("arial.ttf", 36)
            font_text = ImageFont.truetype("arial.ttf", 22)
            font_small = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = font_text = font_small = ImageFont.load_default()

    # ---------- Colors ----------
    gold = (184, 155, 78)
    charcoal = (54, 54, 54)
    neon_cyan = (0, 255, 200)
    border_color = neon_cyan if "neon_border" in equipped_set else gold
    border_width = 4 if "neon_border" in equipped_set else 3

    # ---------- Outer borders ----------
    draw.rounded_rectangle([10, 10, 790, 390], radius=12, outline=border_color, width=border_width)
    draw.rounded_rectangle([18, 18, 782, 382], radius=8, outline=border_color, width=1)

    # ---------- Circular Avatar (left) ----------
    if profile_photo_bytes:
        try:
            avatar = Image.open(io.BytesIO(profile_photo_bytes)).convert("RGBA")
            avatar = avatar.resize((120, 120))
            mask = Image.new("L", (120, 120), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 120, 120), fill=255)
            img.paste(avatar, (40, 80), mask)
        except:
            draw.ellipse([40, 80, 160, 200], fill=(200, 190, 170), outline=border_color, width=4)
            draw.text((100, 140), "?", fill=border_color, font=font_title, anchor="mm")
    else:
        draw.ellipse([40, 80, 160, 200], fill=(200, 190, 170), outline=border_color, width=4)
        draw.text((100, 140), "?", fill=border_color, font=font_title, anchor="mm")

    # Avatar ring
    draw.ellipse([37, 77, 163, 203], outline=border_color, width=4)

    # ---------- Text helper ----------
    def draw_elegant(pos, text, font, fill=charcoal, accent=None):
        x, y = pos
        draw.text((x+1, y+1), text, font=font, fill=(200, 195, 185))
        if accent:
            draw.text((x, y), text, font=font, fill=accent)
        else:
            draw.text((x, y), text, font=font, fill=fill)

    # ---------- User stats (right side) ----------
    name = user_data.get("first_name") or user_data.get("username") or str(user_data["user_id"])
    level = user_data["level"]
    mmr = user_data["mmr"]
    wins = user_data["wins"]
    streak = user_data["streak"]
    total_games = user_data["total_games"]
    rank = user_data.get("rank_tier", "Bronze").upper()

    x_start = 200
    y = 80

    draw_elegant((x_start, y), name, font_title, fill=charcoal)
    y += 50

    draw_elegant((x_start, y), f"Level {level}   •   MMR {mmr}", font_text, accent=gold)
    y += 40

    draw_elegant((x_start, y), f"Wins: {wins} / {total_games}", font_text, fill=charcoal)
    y += 35

    draw_elegant((x_start, y), f"Streak: {streak} 🔥", font_text, fill=charcoal)

    # Rank badge
    draw_elegant((600, 30), rank, font_title, accent=gold)

    # Decorative line
    draw.line([(30, 270), (770, 270)], fill=border_color, width=1)

    # ---------- XP Progress Bar ----------
    current_xp = user_data["xp"]
    next_lvl_xp = xp_for_level(level + 1)
    prev_lvl_xp = xp_for_level(level)
    total_needed = next_lvl_xp - prev_lvl_xp
    if total_needed <= 0:
        progress = 1.0
    else:
        progress = min(1.0, max(0.0, (current_xp - prev_lvl_xp) / total_needed))

    bar_x, bar_y = 60, 300
    bar_width, bar_height = 680, 20
    draw.rounded_rectangle([bar_x, bar_y, bar_x+bar_width, bar_y+bar_height], radius=6, fill=(220, 215, 205))
    fill_color = neon_cyan if "neon_border" in equipped_set else gold
    fill_w = int(bar_width * progress)
    if fill_w > 0:
        draw.rounded_rectangle([bar_x, bar_y, bar_x+fill_w, bar_y+bar_height], radius=6, fill=fill_color)
    xp_text = f"XP: {current_xp} / {next_lvl_xp}"
    draw_elegant((bar_x, bar_y+30), xp_text, font_small, fill=charcoal)

    return img