import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'quiz.db')

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('数据库中的表:')
for table in tables:
    print(f'  {table[0]}')

conn.close()