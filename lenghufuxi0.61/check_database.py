import sqlite3
import os

# 检查数据库文件是否存在
print(f"数据库文件是否存在: {os.path.exists('quiz_system.db')}")

if os.path.exists('quiz_system.db'):
    # 连接数据库
    conn = sqlite3.connect('quiz_system.db')
    cursor = conn.cursor()
    
    # 检查所有表
    print("\n数据库中的表：")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
    
    # 检查用户表
    print("\n用户表内容（前5条）：")
    cursor.execute('SELECT * FROM users LIMIT 5')
    users = cursor.fetchall()
    for user in users:
        print(user)
    
    # 关闭连接
    conn.close()
else:
    print("数据库文件不存在，将检查是否有其他数据库文件")
    # 列出当前目录下的文件
    print("\n当前目录下的文件：")
    for file in os.listdir('.'):
        if file.endswith('.db'):
            print(file)