import sqlite3

conn = sqlite3.connect('quiz_database.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM knowledge LIMIT 10')
columns = [col[0] for col in cursor.description]
rows = cursor.fetchall()

print("知识点表结构：")
print(columns)
print("\n前10条知识点：")
for row in rows:
    print(dict(zip(columns, row)))

conn.close()
