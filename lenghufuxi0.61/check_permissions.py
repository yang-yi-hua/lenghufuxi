import sqlite3

conn = sqlite3.connect('quiz_database.db')
cursor = conn.cursor()

print('=== Users ===')
cursor.execute('SELECT * FROM users')
for row in cursor.fetchall():
    print(row)

print('\n=== Chapters ===')
cursor.execute('SELECT * FROM chapters')
for row in cursor.fetchall():
    print(row)

print('\n=== User Course Permissions ===')
cursor.execute('SELECT * FROM user_course_permissions')
for row in cursor.fetchall():
    print(row)

conn.close()
