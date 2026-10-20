import sqlite3
from pathlib import Path

database_path = Path(__file__).with_name("chat_history.db")

def init_db():
    conn = sqlite3.connect(database_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()

def save_question_answer(question, answer):
    conn = sqlite3.connect(database_path)
    try:
        conn.execute(
            "INSERT INTO questions (question, answer) VALUES (?, ?)",
            (question, answer)
        )
        conn.commit()
    finally:
        conn.close()

def get_question_answers():
    conn = sqlite3.connect(database_path)
    try:
        cursor = conn.execute(
            "SELECT id, question, answer FROM questions ORDER BY id DESC LIMIT 10"
        )
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()