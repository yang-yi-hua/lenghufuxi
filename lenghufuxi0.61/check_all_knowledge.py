import sqlite3

conn = sqlite3.connect('quiz_database.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM knowledge')
columns = [col[0] for col in cursor.description]
rows = cursor.fetchall()

print(f"共有 {len(rows)} 条知识点")
print("\n所有知识点：")
for row in rows:
    kp = dict(zip(columns, row))
    print(f"ID: {kp['id']}, 标题: {kp['title']}, 类别: {kp['category']}, 章节: {kp['chapter_id']}")

conn.close()
