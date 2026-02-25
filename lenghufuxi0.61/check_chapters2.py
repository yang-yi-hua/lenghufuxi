import sqlite3

conn = sqlite3.connect('quiz_database.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM chapters')
columns = [col[0] for col in cursor.description]
rows = cursor.fetchall()

print(f"章节表结构：{columns}")
print(f"\n共有 {len(rows)} 条章节")
print("\n所有章节：")
for row in rows:
    chapter = dict(zip(columns, row))
    print(chapter)

conn.close()
