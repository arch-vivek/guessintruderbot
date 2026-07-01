from models import query_all, query_one
from datetime import date, timedelta

def get_daily_active_users(days=7):
    """Count users whose last_activity was on each day (using users.last_activity)."""
    result = []
    for i in range(days-1, -1, -1):
        d = date.today() - timedelta(days=i)
        row = query_one(
            "SELECT COUNT(*) as cnt FROM users WHERE date(last_activity) = ?",
            (d.isoformat(),)
        )
        result.append({"date": d.isoformat(), "count": row["cnt"] if row else 0})
    return result

def get_games_per_mode():
    """Count matches per mode."""
    rows = query_all(
        "SELECT mode, COUNT(*) as cnt FROM matches GROUP BY mode ORDER BY cnt DESC"
    )
    return [{"mode": r["mode"], "count": r["cnt"]} for r in rows]

def get_xp_earned_over_time(days=7):
    """Placeholder – you can log XP events to a table or CSV. For now, return empty data."""
    result = []
    for i in range(days-1, -1, -1):
        d = date.today() - timedelta(days=i)
        result.append({"date": d.isoformat(), "xp": 0})
    return result

def get_achievement_stats():
    """Count unlocked achievements."""
    rows = query_all(
        "SELECT achievement_id, COUNT(*) as cnt FROM achievements GROUP BY achievement_id"
    )
    return [{"achievement": r["achievement_id"], "count": r["cnt"]} for r in rows]