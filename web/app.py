import json
import os
import io
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, flash, redirect, url_for
from auth import verify_telegram_auth
from decorators import login_required, admin_required
from models import query_one, query_all, execute
from analytics import get_daily_active_users, get_games_per_mode, get_xp_earned_over_time, get_achievement_stats
from config import SECRET_KEY, ADMIN_IDS
from telegram_api import get_cached_photo_url
import logging
from datetime import date

app = Flask(__name__)
app.secret_key = SECRET_KEY
os.makedirs("logs", exist_ok=True)

# Logger
web_logger = logging.getLogger("web")
web_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
web_logger.addHandler(handler)

# ─────────────── Authentication ───────────────
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/auth/callback", methods=["POST"])
def auth_callback():
    data = request.form.to_dict()
    if not verify_telegram_auth(data):
        flash("Invalid authentication.", "danger")
        return redirect(url_for("login"))

    user_id = int(data["id"])
    # Ensure user exists in our DB (they might have used the bot already)
    user = query_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not user:
        # Auto-create user via bot's function? For simplicity, just redirect to login with error
        flash("User not found. Please start the bot first (/start).", "warning")
        return redirect(url_for("login"))

    session["user_id"] = user_id
    session["username"] = data.get("username", f"user{user_id}")
    session["first_name"] = data.get("first_name", "")
    flash("Logged in successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─────────────── User Dashboard ───────────────
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    user = query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    achievements = query_all(
        "SELECT achievement_id, unlocked_at FROM achievements WHERE user_id = ?", (user_id,)
    )
    recent_matches = query_all(
        "SELECT * FROM matches WHERE players LIKE ? ORDER BY created_at DESC LIMIT 5",
        (f"%{user_id}%",)
    )
    return render_template("dashboard.html", user=user, achievements=achievements, recent_matches=recent_matches)

@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    user = query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    photo_url = get_cached_photo_url(user_id)
    return render_template("profile.html", user=user, photo_url=photo_url)

@app.route("/leaderboard")
@login_required
def leaderboard():
    top = query_all("SELECT user_id, username, first_name, level, mmr FROM users ORDER BY mmr DESC LIMIT 20")
    return render_template("leaderboard.html", top=top)

# ─────────────── Admin Panel ───────────────
@app.route("/admin")
@admin_required
def admin_dashboard():
    total_users = query_one("SELECT COUNT(*) as cnt FROM users")["cnt"]
    total_matches = query_one("SELECT COUNT(*) as cnt FROM matches")["cnt"]
    today = date.today().isoformat()
    try:
        active_today = query_one(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM matches WHERE date(created_at) = ?",
            (today,)
        )["cnt"] or 0
    except:
        active_today = 0
    try:
        new_today = query_one(
            "SELECT COUNT(*) as cnt FROM users WHERE date(created_at) = ?",
            (today,)
        )["cnt"] or 0
    except:
        new_today = 0
    return render_template("admin/admin_dashboard.html",
                           total_users=total_users,
                           total_matches=total_matches,
                           active_today=active_today,
                           new_today=new_today)

@app.route("/admin/users")
@admin_required
def admin_users():
    users = query_all("SELECT * FROM users ORDER BY mmr DESC")
    return render_template("admin/users.html", users=users)

@app.route("/admin/user/<int:user_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_user(user_id):
    if request.method == "POST":
        field = request.form["field"]
        value = request.form["value"]
        allowed = {"xp", "level", "mmr", "rank_tier", "wins", "losses", "streak", "max_streak"}
        if field in allowed:
            if field == "rank_tier":
                execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
            else:
                execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (int(value), user_id))
            flash(f"Updated {field} for user {user_id}.", "success")
        else:
            flash("Invalid field.", "danger")
    user = query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return render_template("admin/user_edit.html", user=user)

@app.route("/admin/analytics")
@admin_required
def admin_analytics():
    dau = get_daily_active_users(7)
    modes = get_games_per_mode()
    xp_over_time = get_xp_earned_over_time(7)
    achievement_stats = get_achievement_stats()
    return render_template("admin/analytics.html",
                           dau_json=json.dumps(dau),
                           modes_json=json.dumps(modes),
                           xp_json=json.dumps(xp_over_time),
                           ach_json=json.dumps(achievement_stats))

@app.route("/admin/logs")
@admin_required
def admin_logs():
    try:
        with open("logs/bot.log", "r") as f:
            lines = f.readlines()[-200:]  # last 200 lines
    except:
        lines = ["Log file not found."]
    return render_template("admin/logs.html", lines=lines)

@app.route("/admin/reports")
@admin_required
def admin_reports():
    # Just provide download links for CSV
    return render_template("admin/reports.html")


@app.route("/admin/reports/download/<filename>")
@admin_required
def download_report(filename):
    allowed = {"game_events.csv", "users.csv"}

    if filename not in allowed:
        flash("Unknown report.", "danger")
        return redirect(url_for("admin_reports"))

    # --- Game Events CSV ---
    if filename == "game_events.csv":
        file_path = os.path.join(os.path.dirname(__file__), "..", "logs", "game_events.csv")
        # Create with header if missing
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("timestamp,event_type,user_id,details\n")
        return send_file(file_path, as_attachment=True)

    # --- Users CSV ---
    if filename == "users.csv":
        # Fetch all users from the database
        users = query_all("SELECT * FROM users")
        output = io.StringIO()
        writer = csv.writer(output)

        if users:
            # Get column names from the first row
            column_names = list(users[0].keys())
            writer.writerow(column_names)          # write header
            for row in users:
                # Build a list of values in the same order as column_names
                writer.writerow([row[col] for col in column_names])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype="text/csv",
            as_attachment=True,
            download_name="users.csv"
        )

    # Fallback (should never be reached)
    flash("Unknown report.", "danger")
    return redirect(url_for("admin_reports"))

@app.context_processor
def inject_is_admin():
    return dict(is_admin=("user_id" in session and session["user_id"] in ADMIN_IDS))

@app.route("/dev-login", methods=["GET", "POST"])
def dev_login():
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        if not user_id.isdigit():
            flash("Invalid user ID.", "danger")
            return render_template("dev_login.html")
        user_id = int(user_id)
        user = query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            flash("User not found. Please start the bot first (/start).", "warning")
            return render_template("dev_login.html")
        session["user_id"] = user_id
        session["username"] = user["username"] or f"user{user_id}"
        session["first_name"] = user["first_name"] or ""
        flash("Logged in (dev mode).", "success")
        return redirect(url_for("dashboard"))
    return render_template("dev_login.html")

# ─────────────── Run ───────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)