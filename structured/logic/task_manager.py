# logic/task_manager.py
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
    start_date TEXT, -- yyyy-MM-dd
    end_date TEXT    -- yyyy-MM-dd
);
"""

class TaskManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.conn.row_factory = sqlite3.Row

    def ensure_schema(self):
        self.conn.execute(SCHEMA_SQL)
        self.conn.commit()

    # ===== CRUD / Queries =====
    def fetch_all_min(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, title FROM tasks ORDER BY id ASC")
        return [dict(row) for row in cur.fetchall()]

    def fetch_all_full(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, s_text, m_text, a_text, r_text, start_date, end_date FROM tasks")
        return [dict(row) for row in cur.fetchall()]

    def fetch_one(self, task_id: int) -> Optional[Dict]:
        cur = self.conn.cursor()
        cur.execute("""SELECT id, title, s_text, m_text, a_text, r_text, start_date, end_date
                       FROM tasks WHERE id=?""", (task_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def create_task(self, payload: Dict) -> int:
        cur = self.conn.cursor()
        cur.execute("""INSERT INTO tasks(title, s_text, m_text, a_text, r_text, start_date, end_date)
                       VALUES(?,?,?,?,?,?,?)""",
                    (payload.get("title"),
                     payload.get("s_text"),
                     payload.get("m_text"),
                     payload.get("a_text"),
                     payload.get("r_text"),
                     payload.get("start_date"),
                     payload.get("end_date")))
        self.conn.commit()
        return cur.lastrowid

    def update_task(self, task_id: int, payload: Dict) -> None:
        self.conn.execute("""UPDATE tasks
                             SET title=?, s_text=?, m_text=?, a_text=?, r_text=?, start_date=?, end_date=?
                             WHERE id=?""",
                          (payload.get("title"),
                           payload.get("s_text"),
                           payload.get("m_text"),
                           payload.get("a_text"),
                           payload.get("r_text"),
                           payload.get("start_date"),
                           payload.get("end_date"),
                           task_id))
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()
