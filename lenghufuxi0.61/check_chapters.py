import sqlite3

conn = sqlite3.connect('quiz_database.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM chapters')
columns = [col[0] for col in cursor.description]
rows = cursor.fetchall()

print(f"共有 {len(rows)} 条章节")
print("\n所有章节：")
for row in rows:
    chapter = dict(zip(columns, row))
    print(f"ID: {chapter['id']}, 标题: {chapter['title']}, 父级: {chapter['parent_id']}, 课程: {chapter['course_id']}")

conn.close()
