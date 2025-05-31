import sqlite3

# Connect to the SQLite database (creates file if it doesn't exist)
conn = sqlite3.connect('sympai.db')
c = conn.cursor()

# Drop tables if they exist (optional for dev reset — remove in prod)
c.execute("DROP TABLE IF EXISTS feedback")
c.execute("DROP TABLE IF EXISTS chat_history")

# Create chat history table
c.execute('''
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT NOT NULL,
    sympai_response TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Create feedback table with link to chat_history
c.execute('''
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    feedback TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chat_history(id)
)
''')

conn.commit()
conn.close()

print("✅ Database and tables created successfully.")
