import sqlite3

# 连接数据库
conn = sqlite3.connect('quiz_database.db')
cursor = conn.cursor()

# 删除用户名为????的用户
print("正在删除用户名为????的用户...")
cursor.execute("DELETE FROM users WHERE name LIKE '%?%'")
deleted_count = cursor.rowcount
print(f"删除了 {deleted_count} 个用户")

# 查看剩余用户
print("\n剩余用户：")
cursor.execute("SELECT id, username, name, totalScore FROM users")
users = cursor.fetchall()
for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}, Name: {user[2]}, Score: {user[3]}")

# 提交并关闭连接
conn.commit()
conn.close()
print("\n操作完成！")