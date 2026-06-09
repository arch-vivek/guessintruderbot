SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    language_code TEXT DEFAULT 'en',
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    total_games INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    mmr INTEGER DEFAULT 1200,
    rank_tier TEXT DEFAULT 'bronze',
    season_id INTEGER DEFAULT 1,
    clan_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_daily DATE,
    daily_streak INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS achievements (
    user_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, achievement_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT NOT NULL,
    players TEXT NOT NULL,
    winner_ids TEXT,
    puzzle_set TEXT,
    duration_sec REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_challenges (
    date TEXT PRIMARY KEY,
    puzzle_data TEXT NOT NULL,
    global_highscore INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS seasons (
    season_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    active INTEGER DEFAULT 0
);

CREATE TABLE friendships (
    user_id INTEGER NOT NULL,
    friend_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, accepted, blocked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (friend_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_users_mmr ON users(mmr DESC);
CREATE INDEX IF NOT EXISTS idx_matches_created ON matches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_friendships_user_id ON friendships(user_id);
CREATE INDEX IF NOT EXISTS idx_friendships_friend_id ON friendships(friend_id);
"""

SEED_SEASON = """
INSERT OR IGNORE INTO seasons (season_id, name, start_date, end_date, active)
VALUES (1, 'Genesis', '2025-01-01', '2099-12-31', 1);
"""