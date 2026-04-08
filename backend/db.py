import sqlite3
import os

DB_PATH = "data/database.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_document(user_id: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO documents (user_id, content) VALUES (?, ?)', (user_id, content))
    conn.commit()
    conn.close()

def get_documents(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM documents WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"content": row[0]} for row in rows]
