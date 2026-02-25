import sqlite3

# 连接数据库
conn = sqlite3.connect('quiz_system.db')
cursor = conn.cursor()

# 检查排行榜中的匿名用户记录
print("检查排行榜中的匿名用户记录：")
cursor.execute('SELECT * FROM rankings WHERE name = ?', ('匿名用户',))
anonymous_records = cursor.fetchall()
print(f"找到 {len(anonymous_records)} 条匿名用户记录")

# 显示前5条记录
if anonymous_records:
    print("前5条记录：")
    for record in anonymous_records[:5]:
        print(record)

# 检查排行榜中的所有记录
print("\n检查排行榜中的所有记录（前10条）：")
cursor.execute('SELECT * FROM rankings LIMIT 10')
all_records = cursor.fetchall()
for record in all_records:
    print(record)

# 关闭连接
conn.close()