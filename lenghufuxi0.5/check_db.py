import sqlite3

# 连接到数据库
conn = sqlite3.connect('quiz_database.db')
conn.row_factory = sqlite3.Row

# 创建游标
cursor = conn.cursor()

# 查询章节数据
print('章节数据:')
cursor.execute('SELECT * FROM chapters ORDER BY level, parent_id, id')
chapters = cursor.fetchall()

for chapter in chapters:
    print(dict(chapter))

# 查询知识点数据
print('\n知识点数据:')
cursor.execute('SELECT * FROM knowledge ORDER BY id')
knowledge_items = cursor.fetchall()

for item in knowledge_items:
    print(dict(item))

# 关闭连接
conn.close()