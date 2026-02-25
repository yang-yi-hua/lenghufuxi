import sqlite3

conn = sqlite3.connect('quiz.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM science_encyclopedia')
count = cursor.fetchone()[0]
print(f'Science count: {count}')

if count > 0:
    cursor.execute('SELECT id, title, category FROM science_encyclopedia LIMIT 5')
    items = cursor.fetchall()
    print('Sample items:')
    for item in items:
        print(f'  {item}')

conn.close()