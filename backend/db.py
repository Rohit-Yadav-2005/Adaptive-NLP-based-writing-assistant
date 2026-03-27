import sqlite3

DB_PATH="data/app.db"

def init_db():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_document(user_id,text):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    c.execute(
        "INSERT INTO documents(user_id,content) VALUES(?,?)",
        (user_id,text)
    )

    conn.commit()
    conn.close()


def get_documents(user_id):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()

    c.execute(
        "SELECT id,content FROM documents WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )

    data=c.fetchall()
    conn.close()

    return data