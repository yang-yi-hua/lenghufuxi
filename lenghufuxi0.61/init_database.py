import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'quiz.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT UNIQUE,
            totalScore INTEGER DEFAULT 0
        )
    ''')
    
    # 创建章节表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            level INTEGER,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES chapters (id) ON DELETE CASCADE
        )
    ''')
    
    # 创建知识点表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category TEXT,
            image TEXT,
            course_code TEXT,
            chapter_id INTEGER
        )
    ''')
    
    # 创建排行榜表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            score INTEGER,
            correctCount INTEGER,
            time INTEGER,
            date TEXT
        )
    ''')
    
    # 创建用户课程权限表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_course_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chapter_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE,
            UNIQUE(user_id, chapter_id)
        )
    ''')
    
    # 创建用户答题时间记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quiz_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chapter_id INTEGER,
            last_quiz_time TEXT,
            next_available_time TEXT,
            interval_days INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE,
            UNIQUE(user_id, chapter_id)
        )
    ''')
    
    # 创建PK挑战表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pk_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger_id INTEGER,
            opponent_id INTEGER,
            status TEXT DEFAULT 'pending',
            challenger_score INTEGER DEFAULT 0,
            opponent_score INTEGER DEFAULT 0,
            current_question INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 10,
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (challenger_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (opponent_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # 创建BOSS挑战表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS boss_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            boss_name TEXT,
            boss_hp INTEGER,
            boss_max_hp INTEGER,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # 创建BOSS挑战参与记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS boss_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boss_id INTEGER,
            user_id INTEGER,
            correct_count INTEGER DEFAULT 0,
            received_reward INTEGER DEFAULT 0,
            FOREIGN KEY (boss_id) REFERENCES boss_challenges (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(boss_id, user_id)
        )
    ''')
    
    # 创建科学百科知识表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS science_encyclopedia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category TEXT,
            difficulty TEXT DEFAULT 'easy',
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print('数据库表初始化完成！')

if __name__ == '__main__':
    init_database()