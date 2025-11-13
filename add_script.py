# seed_test_data.py
import sqlite3
from datetime import date, timedelta

DB_FILE = "smart_planner.db"


def ensure_schema(conn):
    c = conn.cursor()
    c.execute("""
     CREATE TABLE IF NOT EXISTS tasks(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         title TEXT NOT NULL,
         s_text TEXT,
         m_text TEXT,
         a_text TEXT,
         r_text TEXT,
         start_date TEXT,
         end_date   TEXT
     )
     """)
    conn.commit()


def add_samples(conn):
    today = date.today()

    samples = [
        {
            "title": "Закрыть БД",
            "S": "Подготовить и сдать лабораторную по БД.",
            "M": "Отчёт принят, оценка ≥ 4.",
            "A": "Есть черновик, время на доработку — 2 вечера.",
            "R": "Нужно для зачёта и допуска.",
            "start": today + timedelta(days=1),
            "end": today + timedelta(days=8),
        },
        {
            "title": "Диплом — глава 1",
            "S": "Написать обзор литературы.",
            "M": "Объём 8–12 страниц, 10+ источников.",
            "A": "Материалы собраны в Zotero.",
            "R": "Основа для остальных глав.",
            "start": today - timedelta(days=5),
            "end": today + timedelta(days=10),
        },
        {
            "title": "Подготовка к экзамену",
            "S": "Разобрать 30 билетов.",
            "M": "Минимум 2 билета в день.",
            "A": "План-график составлен.",
            "R": "Экзамен через месяц.",
            "start": today,
            "end": today + timedelta(days=30),
        },
        {
            "title": "Однодневная задача",
            "S": "Сделать резервную копию проекта.",
            "M": "Архив в облаке, лог успешной копии.",
            "A": "Скрипт готов.",
            "R": "Снизить риски перед релизом.",
            "start": today + timedelta(days=3),
            "end": today + timedelta(days=3),
        },
        {
            "title": "Долгая задача",
            "S": "Реализовать модуль отчётности.",
            "M": "3 отчёта и 5 графиков.",
            "A": "Команда 2 человека.",
            "R": "Для руководства и инвесторов.",
            "start": today - timedelta(days=20),
            "end": today + timedelta(days=60),
        },
    ]

    c = conn.cursor()
    for s in samples:
        c.execute("""
             INSERT INTO tasks(title, s_text, m_text, a_text, r_text, start_date, end_date)
             VALUES (?, ?, ?, ?, ?, ?, ?)
         """, (
            s["title"], s["S"], s["M"], s["A"], s["R"],
            s["start"].strftime("%Y-%m-%d"),
            s["end"].strftime("%Y-%m-%d"),
        ))
    conn.commit()


if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    ensure_schema(conn)
    add_samples(conn)
    conn.close()
    print("Тестовые записи добавлены.")
