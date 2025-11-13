import sqlite3
from typing import List, Dict, Optional

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    s_text TEXT,
    m_text TEXT,
    a_text TEXT,
    r_text TEXT,
    start_date TEXT,
    end_date TEXT
);
"""


def connect(db_file: str):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn):
    conn.execute(SCHEMA_SQL)
    conn.commit()


def fetch_all_min(conn) -> List[Dict]:
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM tasks ORDER BY id ASC")
    return [dict(row) for row in cur.fetchall()]


def fetch_all_full(conn) -> List[Dict]:
    cur = conn.cursor()
    cur.execute("SELECT id, title, s_text, m_text, a_text, r_text, start_date, end_date FROM tasks")
    return [dict(row) for row in cur.fetchall()]


def fetch_one(conn, task_id: int) -> Optional[Dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, s_text, m_text, a_text, r_text, start_date, end_date FROM tasks WHERE id=?",
        (task_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def create_task(conn, payload: Dict) -> int:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO tasks(title, s_text, m_text, a_text, r_text, start_date, end_date)
           VALUES(?,?,?,?,?,?,?)""",
        (
            payload.get("title"),
            payload.get("s_text"),
            payload.get("m_text"),
            payload.get("a_text"),
            payload.get("r_text"),
            payload.get("start_date"),
            payload.get("end_date"),
        ),
    )
    conn.commit()
    return cur.lastrowid


def update_task(conn, task_id: int, payload: Dict):
    conn.execute(
        """UPDATE tasks SET title=?, s_text=?, m_text=?, a_text=?, r_text=?, start_date=?, end_date=? 
           WHERE id=?""",
        (
            payload.get("title"),
            payload.get("s_text"),
            payload.get("m_text"),
            payload.get("a_text"),
            payload.get("r_text"),
            payload.get("start_date"),
            payload.get("end_date"),
            task_id,
        ),
    )
    conn.commit()


def delete_task(conn, task_id: int):
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
