import os

SECRET_KEY = os.getenv("WEB_SECRET_KEY", "change-me-in-production")
BOT_TOKEN = os.getenv("BOT_TOKEN")   # same as the bot uses
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "game.db")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]