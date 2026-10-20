import sqlite3
from pathlib import Path

database_path = Path(__file__).with_name("practice.db")
conn = sqlite3.connect(database_path)

conn.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )
""")

def save_question_answer(question, answer):
    conn.execute(
        "INSERT INTO questions (question, answer) VALUES (?, ?)",
        (question, answer)
    )
    conn.commit()

save_question_answer(
    "为什么要使用函数？",
    "把重复的操作整理起来，传入不同的数据就能重复使用。"
)

cursor = conn.execute("SELECT id, question, answer FROM questions")
rows = cursor.fetchall()
print(rows)

conn.close()