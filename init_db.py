import sqlite3

conn = sqlite3.connect("sympai.db")
cursor = conn.cursor()

# 💣 Drop old tables if they exist
cursor.execute('DROP TABLE IF EXISTS chat_history')
cursor.execute('DROP TABLE IF EXISTS feedback')

# 🧱 Recreate with correct schema
cursor.execute('''
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT,
    sympai_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER,
    feedback TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
print("✅ Fresh database created with correct schema.")
