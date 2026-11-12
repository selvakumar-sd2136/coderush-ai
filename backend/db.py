import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), "coderush.db")

def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER);
        CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, topic TEXT, level TEXT, language TEXT, data TEXT);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER, question_id INTEGER, level INTEGER,
            started_at REAL, time_taken REAL, result TEXT, hints_used INTEGER DEFAULT 0, score INTEGER DEFAULT 0,
            created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, attempt_id INTEGER, text TEXT);
        CREATE TABLE IF NOT EXISTS progress(user_id INTEGER PRIMARY KEY, current_level INTEGER DEFAULT 1,
            completed INTEGER DEFAULT 0, score INTEGER DEFAULT 0);
        """)

def execute(sql, args=()):
    with _conn() as c:
        return c.execute(sql, args).lastrowid

def one(sql, args=()):
    with _conn() as c:
        r = c.execute(sql, args).fetchone()
        return dict(r) if r else None

def many(sql, args=()):
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]
