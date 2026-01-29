from flask import Flask, request, jsonify, send_from_directory
import json
import os
import sqlite3

# 获取当前目录的绝对路径
BASE_DIR = os.path.abspath('.')

# 创建Flask应用
app = Flask(__name__)

# 手动添加CORS支持
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# SQLite数据库文件路径 - 存储到项目文件夹内
DB_FILE = os.path.join(BASE_DIR, 'quiz_database.db')

# 数据文件路径（保留，用于兼容旧数据）
DATA_FILE = os.path.join(BASE_DIR, 'quiz_data.json')

# 初始化数据文件（保留，用于兼容旧数据）
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'rankings': []
            }, f, ensure_ascii=False, indent=2)

# 初始化SQLite数据库
init_data()

# 创建SQLite数据库连接
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# 创建数据库表
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
            level INTEGER,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES chapters (id) ON DELETE CASCADE
        )
    ''')
    
    # 创建知识点表（添加章节关联）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category TEXT,
            image TEXT
        )
    ''')
    
    # 为现有表添加chapter_id列（如果不存在）
    try:
        cursor.execute('ALTER TABLE knowledge ADD COLUMN chapter_id INTEGER')
        # 添加外键约束（注意：SQLite不支持直接添加外键约束到现有表）
    except:
        pass  # 如果列已存在，忽略错误
    
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
    
    # 插入默认的第一级章节
    cursor.execute('SELECT COUNT(*) FROM chapters WHERE level = 1')
    if cursor.fetchone()[0] == 0:
        default_chapters = [
            {'name': '科学', 'level': 1},
            {'name': '着陆', 'level': 1},
            {'name': '探索', 'level': 1},
            {'name': '星辰', 'level': 1},
            {'name': '5D物理', 'level': 1},
            {'name': '火箭', 'level': 1},
            {'name': '科创', 'level': 1}
        ]
        
        for chapter in default_chapters:
            cursor.execute('''
                INSERT INTO chapters (name, level, parent_id)
                VALUES (?, ?, ?)
            ''', (chapter['name'], chapter['level'], None))
    
    conn.commit()
    conn.close()

# 初始化数据库
init_database()

# 加载数据（保留，用于兼容旧数据）
def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# 保存数据（保留，用于兼容旧数据）
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 根路径返回index.html
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

# 静态文件服务
def serve_file(filepath):
    """Serve static files"""
    full_path = os.path.join(BASE_DIR, filepath)
    if os.path.exists(full_path):
        return send_from_directory(BASE_DIR, filepath)
    return f"File not found: {filepath}", 404

# 样式文件
@app.route('/style.css')
def style():
    return serve_file('style.css')

# JavaScript文件
@app.route('/script.js')
def script():
    return serve_file('script.js')

# 题库文件
@app.route('/science-questions.json')
def questions_file():
    return serve_file('science-questions.json')

# 获取排行榜
@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从用户表中获取排名数据
    cursor.execute('''
        SELECT name, totalScore as score, 0 as correctCount, 0 as time, datetime('now') as date
        FROM users
        ORDER BY totalScore DESC
        LIMIT 20
    ''')
    rankings = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(rankings)

# 清空排行榜
@app.route('/api/clear-rankings', methods=['POST'])
def clear_rankings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 清空排行榜表
    cursor.execute('DELETE FROM rankings')
    
    # 重置所有用户积分
    cursor.execute('UPDATE users SET totalScore = 0')
    
    # 同时更新旧的数据文件
    clear_data = {
        'rankings': []
    }
    save_data(clear_data)
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': '排行榜已清空'})

# 提交分数
@app.route('/api/submit', methods=['POST'])
def submit_score():
    ranking_data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 添加排名记录到排行榜表
    cursor.execute('''
        INSERT INTO rankings (name, score, correctCount, time, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (ranking_data['name'], ranking_data['score'], ranking_data['correctCount'], ranking_data['time'], ranking_data['date']))
    
    # 更新用户积分
    cursor.execute('UPDATE users SET totalScore = totalScore + ? WHERE name = ?', (ranking_data['score'], ranking_data['name']))
    
    # 同时更新旧的数据文件（兼容旧系统）
    data = load_data()
    # 按用户名聚合积分
    # 创建用户积分映射
    user_scores = {}
    
    # 先添加现有排名数据
    for record in data['rankings']:
        username = record['name']
        if username not in user_scores:
            user_scores[username] = {
                'name': username,
                'totalScore': record.get('totalScore', record['score']),
                'correctCount': record.get('correctCount', record['correctCount']),
                'lastTime': record['time'],
                'lastDate': record['date']
            }
        else:
            # 如果已有记录，保留较高的总分
            if record.get('totalScore', record['score']) > user_scores[username]['totalScore']:
                user_scores[username] = {
                    'name': username,
                    'totalScore': record.get('totalScore', record['score']),
                    'correctCount': record.get('correctCount', record['correctCount']),
                    'lastTime': record['time'],
                    'lastDate': record['date']
                }
    
    # 添加新的排名数据
    username = ranking_data['name']
    if username not in user_scores:
        # 新用户，直接添加
        user_scores[username] = {
            'name': username,
            'totalScore': ranking_data['score'],
            'correctCount': ranking_data['correctCount'],
            'lastTime': ranking_data['time'],
            'lastDate': ranking_data['date']
        }
    else:
        # 现有用户，累计积分
        user_scores[username]['totalScore'] += ranking_data['score']
        user_scores[username]['correctCount'] += ranking_data['correctCount']
        user_scores[username]['lastTime'] = ranking_data['time']
        user_scores[username]['lastDate'] = ranking_data['date']
    
    # 转换为排名列表格式
    new_rankings = []
    for username, data in user_scores.items():
        new_rankings.append({
            'name': data['name'],
            'score': data['totalScore'],  # 使用累计总分
            'correctCount': data['correctCount'],
            'time': data['lastTime'],
            'date': data['lastDate']
        })
    
    # 按得分降序排序，得分相同则按时间升序
    new_rankings.sort(key=lambda x: (-x['score'], x['time']))
    
    # 只保留前20名
    new_rankings = new_rankings[:20]
    
    # 保存更新后的排名
    save_data({'rankings': new_rankings})
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': '分数提交成功'})

# 获取题库
@app.route('/api/questions', methods=['GET'])
def get_questions():
    questions_path = os.path.join(BASE_DIR, 'science-questions.json')
    with open(questions_path, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

# 知识库管理API

# 初始化知识库
@app.route('/api/knowledge/init', methods=['POST'])
def init_knowledge_base():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查是否已有知识点
    cursor.execute('SELECT COUNT(*) FROM knowledge')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # 从现有文件内容创建
        initial_data = [
            {
                "title": "太阳系行星",
                "content": "太阳系中有八大行星，按距离太阳由近到远依次为：水星、金星、地球、火星、木星、土星、天王星、海王星。",
                "image": "",
                "category": "天文"
            },
            {
                "title": "水的三态变化",
                "content": "水有三种状态：固态（冰）、液态（水）、气态（水蒸气）。三态变化是物理变化，由温度变化引起。",
                "image": "",
                "category": "物理"
            },
            {
                "title": "哺乳动物特征",
                "content": "哺乳动物的主要特征：胎生、哺乳、体表被毛、体温恒定、心脏四腔。",
                "image": "",
                "category": "生物"
            },
            {
                "title": "光合作用",
                "content": "光合作用是植物利用光能将二氧化碳和水转化为有机物并释放氧气的过程，主要场所是叶绿体。",
                "image": "",
                "category": "生物"
            },
            {
                "title": "简单机械",
                "content": "简单机械包括：杠杆、滑轮、轮轴、斜面、楔、螺旋。",
                "image": "",
                "category": "物理"
            },
            {
                "title": "声音传播介质",
                "content": "声音需要介质传播，介质密度越大，传播速度越快。声音不能在真空中传播。",
                "image": "",
                "category": "物理"
            },
            {
                "title": "导体与绝缘体",
                "content": "导体是容易导电的物质，如金属、人体、大地等；绝缘体是不容易导电的物质，如塑料、橡胶、玻璃等。",
                "image": "",
                "category": "物理"
            },
            {
                "title": "地球自转",
                "content": "地球自西向东自转，周期约为24小时，产生昼夜交替现象。",
                "image": "",
                "category": "地理"
            },
            {
                "title": "可再生能源",
                "content": "可再生能源是可以不断再生的能源，如太阳能、风能、水能、生物质能等。",
                "image": "",
                "category": "能源"
            },
            {
                "title": "呼吸系统",
                "content": "人体呼吸系统包括呼吸道和肺，肺是气体交换的主要场所。",
                "image": "",
                "category": "生物"
            }
        ]
        
        # 插入初始知识点
        for item in initial_data:
            cursor.execute('''
                INSERT INTO knowledge (title, content, category, image)
                VALUES (?, ?, ?, ?)
            ''', (item['title'], item['content'], item['category'], item['image']))
        
        conn.commit()
    
    conn.close()
    return jsonify({'status': 'success', 'message': '知识库初始化成功'})

# 加载知识库
@app.route('/api/knowledge', methods=['GET'])
def get_knowledge_base():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有知识点
    cursor.execute('SELECT * FROM knowledge')
    knowledge_base = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(knowledge_base)

# 获取单个知识点
@app.route('/api/knowledge/<int:knowledge_id>', methods=['GET'])
def get_knowledge(knowledge_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取单个知识点
    cursor.execute('SELECT * FROM knowledge WHERE id = ?', (knowledge_id,))
    knowledge = cursor.fetchone()
    
    conn.close()
    
    if knowledge:
        return jsonify(dict(knowledge))
    else:
        return jsonify({'error': '知识点不存在'}), 404

# 添加知识点
@app.route('/api/knowledge', methods=['POST'])
def add_knowledge():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取新知识点数据
    new_knowledge = request.json
    
    # 插入知识点
    cursor.execute('''
        INSERT INTO knowledge (title, content, category, image, chapter_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (new_knowledge['title'], new_knowledge['content'], new_knowledge['category'], new_knowledge.get('image', ''), new_knowledge.get('chapter_id')))
    
    conn.commit()
    new_knowledge_id = cursor.lastrowid
    
    # 获取新创建的知识点
    cursor.execute('SELECT * FROM knowledge WHERE id = ?', (new_knowledge_id,))
    created_knowledge = dict(cursor.fetchone())
    
    conn.close()
    
    return jsonify(created_knowledge), 201

# 更新知识点
@app.route('/api/knowledge/<int:knowledge_id>', methods=['PUT'])
def update_knowledge(knowledge_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取更新数据
    updated_data = request.json
    
    # 更新知识点
    cursor.execute('''
        UPDATE knowledge SET title = ?, content = ?, category = ?, image = ?, chapter_id = ?
        WHERE id = ?
    ''', (updated_data['title'], updated_data['content'], updated_data['category'], updated_data.get('image', ''), updated_data.get('chapter_id'), knowledge_id))
    
    # 检查是否有行被更新
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': '知识点不存在'}), 404
    
    # 获取更新后的知识点
    cursor.execute('SELECT * FROM knowledge WHERE id = ?', (knowledge_id,))
    updated_knowledge = dict(cursor.fetchone())
    
    conn.commit()
    conn.close()
    
    return jsonify(updated_knowledge)

# 删除知识点
@app.route('/api/knowledge/<int:knowledge_id>', methods=['DELETE'])
def delete_knowledge(knowledge_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 删除知识点
    cursor.execute('DELETE FROM knowledge WHERE id = ?', (knowledge_id,))
    
    # 检查是否有行被删除
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': '知识点不存在'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': '知识点删除成功'})

# 章节管理API

# 获取所有章节
@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有章节
    cursor.execute('SELECT * FROM chapters')
    chapters = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(chapters)

# 获取单个章节
@app.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取单个章节
    cursor.execute('SELECT * FROM chapters WHERE id = ?', (chapter_id,))
    chapter = cursor.fetchone()
    
    conn.close()
    
    if chapter:
        return jsonify(dict(chapter))
    else:
        return jsonify({'error': '章节不存在'}), 404

# 添加章节
@app.route('/api/chapters', methods=['POST'])
def add_chapter():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取新章节数据
    new_chapter = request.json
    
    # 插入章节
    cursor.execute('''
        INSERT INTO chapters (name, level, parent_id)
        VALUES (?, ?, ?)
    ''', (new_chapter['name'], new_chapter['level'], new_chapter.get('parent_id')))
    
    conn.commit()
    new_chapter_id = cursor.lastrowid
    
    # 获取新创建的章节
    cursor.execute('SELECT * FROM chapters WHERE id = ?', (new_chapter_id,))
    created_chapter = dict(cursor.fetchone())
    
    conn.close()
    
    return jsonify(created_chapter), 201

# 更新章节
@app.route('/api/chapters/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取更新数据
    updated_data = request.json
    
    # 更新章节
    cursor.execute('''
        UPDATE chapters SET name = ?, level = ?, parent_id = ?
        WHERE id = ?
    ''', (updated_data['name'], updated_data['level'], updated_data.get('parent_id'), chapter_id))
    
    # 检查是否有行被更新
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': '章节不存在'}), 404
    
    # 获取更新后的章节
    cursor.execute('SELECT * FROM chapters WHERE id = ?', (chapter_id,))
    updated_chapter = dict(cursor.fetchone())
    
    conn.commit()
    conn.close()
    
    return jsonify(updated_chapter)

# 删除章节
@app.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 删除章节（级联删除子章节）
    cursor.execute('DELETE FROM chapters WHERE id = ?', (chapter_id,))
    
    # 检查是否有行被删除
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': '章节不存在'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': '章节删除成功'})

# AI生成题目（模拟）
@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    # 模拟AI生成题目，实际项目中可以接入AI模型
    import random
    import time
    
    # 设置随机种子，确保每次生成的题目都是真正随机的
    random.seed(time.time())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从数据库获取所有知识点
    cursor.execute('SELECT * FROM knowledge')
    knowledge_points = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 固定题库（可扩展为基于知识点动态生成）
    all_questions = [
        {
            "question": "太阳系中距离太阳最近的行星是？",
            "options": ["水星", "金星", "地球", "火星"],
            "answer": 0,
            "category": "天文",
            "explanation": "太阳系中八大行星按距离太阳由近到远依次为：水星、金星、地球、火星、木星、土星、天王星、海王星。所以距离太阳最近的行星是水星。"
        },
        {
            "question": "水的三种状态不包括？",
            "options": ["固态", "液态", "气态", "等离子态"],
            "answer": 3,
            "category": "物理",
            "explanation": "水有三种状态：固态（冰）、液态（水）、气态（水蒸气）。等离子态是物质的第四种状态，不属于水的基本三态变化。"
        },
        {
            "question": "哺乳动物的主要特征是什么？",
            "options": ["胎生哺乳", "卵生", "冷血", "体表有鳞片"],
            "answer": 0,
            "category": "生物",
            "explanation": "哺乳动物的主要特征包括：胎生、哺乳、体表被毛、体温恒定、心脏四腔。卵生是爬行动物和鸟类的特征，冷血是爬行动物、鱼类等的特征，体表有鳞片是爬行动物的特征。"
        },
        {
            "question": "光合作用的主要场所是？",
            "options": ["叶绿体", "线粒体", "细胞核", "细胞质"],
            "answer": 0,
            "category": "生物",
            "explanation": "光合作用是植物利用光能将二氧化碳和水转化为有机物并释放氧气的过程，主要场所是叶绿体。线粒体是呼吸作用的主要场所，细胞核是遗传信息库，细胞质是细胞代谢的主要场所。"
        },
        {
            "question": "以下哪项不属于简单机械？",
            "options": ["杠杆", "滑轮", "蒸汽机", "斜面"],
            "answer": 2,
            "category": "物理",
            "explanation": "简单机械包括：杠杆、滑轮、轮轴、斜面、楔、螺旋。蒸汽机是一种复杂的热机，不属于简单机械。"
        },
        {
            "question": "声音不能在以下哪种介质中传播？",
            "options": ["空气", "水", "真空", "金属"],
            "answer": 2,
            "category": "物理",
            "explanation": "声音需要介质传播，介质密度越大，传播速度越快。声音不能在真空中传播，因为真空中没有物质粒子来传递声波。"
        },
        {
            "question": "以下哪种物质是导体？",
            "options": ["塑料", "橡胶", "铜", "玻璃"],
            "answer": 2,
            "category": "物理",
            "explanation": "导体是容易导电的物质，如金属、人体、大地等；绝缘体是不容易导电的物质，如塑料、橡胶、玻璃等。铜是金属，属于导体。"
        },
        {
            "question": "地球自转产生了什么现象？",
            "options": ["四季变化", "昼夜交替", "潮汐", "极光"],
            "answer": 1,
            "category": "地理",
            "explanation": "地球自西向东自转，周期约为24小时，产生昼夜交替现象。四季变化是由地球公转引起的，潮汐是由月球和太阳的引力引起的，极光是由太阳活动引起的。"
        },
        {
            "question": "以下哪项是可再生能源？",
            "options": ["煤炭", "石油", "太阳能", "天然气"],
            "answer": 2,
            "category": "能源",
            "explanation": "可再生能源是可以不断再生的能源，如太阳能、风能、水能、生物质能等。煤炭、石油、天然气属于化石燃料，是不可再生能源。"
        },
        {
            "question": "人体气体交换的主要场所是？",
            "options": ["鼻腔", "喉咙", "肺", "气管"],
            "answer": 2,
            "category": "生物",
            "explanation": "人体呼吸系统包括呼吸道和肺，肺是气体交换的主要场所。鼻腔、喉咙和气管是呼吸道的组成部分，主要作用是过滤、温暖和湿润空气。"
        },
        # 新增题目，丰富题库
        {
            "question": "以下哪项是八大行星中体积最大的？",
            "options": ["地球", "木星", "土星", "天王星"],
            "answer": 1,
            "category": "天文",
            "explanation": "木星是太阳系中体积最大的行星，其直径约为14.3万公里，是地球直径的11倍。"
        },
        {
            "question": "以下哪项是植物进行光合作用的原料？",
            "options": ["氧气和水", "二氧化碳和水", "氧气和二氧化碳", "水和无机盐"],
            "answer": 1,
            "category": "生物",
            "explanation": "光合作用的原料是二氧化碳和水，产物是有机物和氧气。"
        },
        {
            "question": "以下哪项是简单机械中的轮轴？",
            "options": ["剪刀", "螺丝钉", "方向盘", "天平"],
            "answer": 2,
            "category": "物理",
            "explanation": "轮轴是由轮和轴组成的简单机械，方向盘是典型的轮轴应用。"
        },
        {
            "question": "以下哪项是绝缘体？",
            "options": ["铝", "石墨", "陶瓷", "盐水"],
            "answer": 2,
            "category": "物理",
            "explanation": "陶瓷是良好的绝缘体，常用于电气设备的绝缘材料。"
        },
        {
            "question": "以下哪项是不可再生能源？",
            "options": ["风能", "水能", "核能", "太阳能"],
            "answer": 2,
            "category": "能源",
            "explanation": "核能依赖于放射性物质，这些物质是有限的，因此核能属于不可再生能源。"
        },
        {
            "question": "地球公转产生了什么现象？",
            "options": ["四季变化", "昼夜交替", "潮汐", "极光"],
            "answer": 0,
            "category": "地理",
            "explanation": "地球绕太阳公转，由于地轴倾斜，导致太阳直射点在南北回归线之间移动，从而产生四季变化。"
        },
        {
            "question": "以下哪项是人体的主要消化器官？",
            "options": ["心脏", "肺", "胃", "肾脏"],
            "answer": 2,
            "category": "生物",
            "explanation": "胃是人体的主要消化器官之一，负责初步消化食物，尤其是蛋白质。"
        },
        {
            "question": "以下哪项是导体？",
            "options": ["木材", "玻璃", "铁", "橡胶"],
            "answer": 2,
            "category": "物理",
            "explanation": "铁是金属，属于导体，能够导电。木材、玻璃和橡胶都是绝缘体。"
        },
        {
            "question": "以下哪项是太阳系中的矮行星？",
            "options": ["水星", "金星", "冥王星", "火星"],
            "answer": 2,
            "category": "天文",
            "explanation": "冥王星在2006年被重新分类为矮行星，不再被视为太阳系的第八大行星。"
        },
        {
            "question": "以下哪项是简单机械？",
            "options": ["汽车", "飞机", "杠杆", "电脑"],
            "answer": 2,
            "category": "物理",
            "explanation": "杠杆是一种简单机械，由支点、动力臂和阻力臂组成，能够省力或改变力的方向。"
        }
    ]
    
    # 随机打乱题目顺序
    random.shuffle(all_questions)
    
    # 随机选择5道题
    generated_questions = all_questions[:5]
    
    # 为每道题添加唯一ID和随机生成的标识符，确保每次题目不同
    for i, question in enumerate(generated_questions):
        question["id"] = i + 1
        # 添加随机标识符，确保前端能识别到题目变化
        question["quiz_id"] = random.randint(100000, 999999)
    
    return jsonify(generated_questions)

# 按章节生成题目
@app.route('/api/generate-questions-by-chapter', methods=['POST'])
def generate_questions_by_chapter():
    # 模拟AI生成题目，实际项目中可以接入AI模型
    import random
    import time
    
    # 设置随机种子，确保每次生成的题目都是真正随机的
    random.seed(time.time())
    
    # 获取章节参数
    chapter_params = request.json
    first_level_id = chapter_params.get('first_level_id')
    second_level_id = chapter_params.get('second_level_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从数据库获取对应章节的知识点
    if second_level_id:
        # 按第二级章节获取知识点
        cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (second_level_id,))
    else:
        # 按第一级章节获取知识点（只从该章节直接获取，不包括其下的第二级章节）
        cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (first_level_id,))
    
    knowledge_points = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 固定题库（可扩展为基于知识点动态生成）
    all_questions = [
        {
            "question": "太阳系中距离太阳最近的行星是？",
            "options": ["水星", "金星", "地球", "火星"],
            "answer": 0,
            "category": "天文",
            "explanation": "太阳系中八大行星按距离太阳由近到远依次为：水星、金星、地球、火星、木星、土星、天王星、海王星。所以距离太阳最近的行星是水星。"
        },
        {
            "question": "水的三种状态不包括？",
            "options": ["固态", "液态", "气态", "等离子态"],
            "answer": 3,
            "category": "物理",
            "explanation": "水有三种状态：固态（冰）、液态（水）、气态（水蒸气）。等离子态是物质的第四种状态，不属于水的基本三态变化。"
        },
        {
            "question": "哺乳动物的主要特征是什么？",
            "options": ["胎生哺乳", "卵生", "冷血", "体表有鳞片"],
            "answer": 0,
            "category": "生物",
            "explanation": "哺乳动物的主要特征包括：胎生、哺乳、体表被毛、体温恒定、心脏四腔。卵生是爬行动物和鸟类的特征，冷血是爬行动物、鱼类等的特征，体表有鳞片是爬行动物的特征。"
        },
        {
            "question": "光合作用的主要场所是？",
            "options": ["叶绿体", "线粒体", "细胞核", "细胞质"],
            "answer": 0,
            "category": "生物",
            "explanation": "光合作用是植物利用光能将二氧化碳和水转化为有机物并释放氧气的过程，主要场所是叶绿体。线粒体是呼吸作用的主要场所，细胞核是遗传信息库，细胞质是细胞代谢的主要场所。"
        },
        {
            "question": "以下哪项不属于简单机械？",
            "options": ["杠杆", "滑轮", "蒸汽机", "斜面"],
            "answer": 2,
            "category": "物理",
            "explanation": "简单机械包括：杠杆、滑轮、轮轴、斜面、楔、螺旋。蒸汽机是一种复杂的热机，不属于简单机械。"
        },
        {
            "question": "声音不能在以下哪种介质中传播？",
            "options": ["空气", "水", "真空", "金属"],
            "answer": 2,
            "category": "物理",
            "explanation": "声音需要介质传播，介质密度越大，传播速度越快。声音不能在真空中传播，因为真空中没有物质粒子来传递声波。"
        },
        {
            "question": "以下哪种物质是导体？",
            "options": ["塑料", "橡胶", "铜", "玻璃"],
            "answer": 2,
            "category": "物理",
            "explanation": "导体是容易导电的物质，如金属、人体、大地等；绝缘体是不容易导电的物质，如塑料、橡胶、玻璃等。铜是金属，属于导体。"
        },
        {
            "question": "地球自转产生了什么现象？",
            "options": ["四季变化", "昼夜交替", "潮汐", "极光"],
            "answer": 1,
            "category": "地理",
            "explanation": "地球自西向东自转，周期约为24小时，产生昼夜交替现象。四季变化是由地球公转引起的，潮汐是由月球和太阳的引力引起的，极光是由太阳活动引起的。"
        },
        {
            "question": "以下哪项是可再生能源？",
            "options": ["煤炭", "石油", "太阳能", "天然气"],
            "answer": 2,
            "category": "能源",
            "explanation": "可再生能源是可以不断再生的能源，如太阳能、风能、水能、生物质能等。煤炭、石油、天然气属于化石燃料，是不可再生能源。"
        },
        {
            "question": "人体气体交换的主要场所是？",
            "options": ["鼻腔", "喉咙", "肺", "气管"],
            "answer": 2,
            "category": "生物",
            "explanation": "人体呼吸系统包括呼吸道和肺，肺是气体交换的主要场所。鼻腔、喉咙和气管是呼吸道的组成部分，主要作用是过滤、温暖和湿润空气。"
        },
        # 新增题目，丰富题库
        {
            "question": "以下哪项是八大行星中体积最大的？",
            "options": ["地球", "木星", "土星", "天王星"],
            "answer": 1,
            "category": "天文",
            "explanation": "木星是太阳系中体积最大的行星，其直径约为14.3万公里，是地球直径的11倍。"
        },
        {
            "question": "以下哪项是植物进行光合作用的原料？",
            "options": ["氧气和水", "二氧化碳和水", "氧气和二氧化碳", "水和无机盐"],
            "answer": 1,
            "category": "生物",
            "explanation": "光合作用的原料是二氧化碳和水，产物是有机物和氧气。"
        },
        {
            "question": "以下哪项是简单机械中的轮轴？",
            "options": ["剪刀", "螺丝钉", "方向盘", "天平"],
            "answer": 2,
            "category": "物理",
            "explanation": "轮轴是由轮和轴组成的简单机械，方向盘是典型的轮轴应用。"
        },
        {
            "question": "以下哪项是绝缘体？",
            "options": ["铝", "石墨", "陶瓷", "盐水"],
            "answer": 2,
            "category": "物理",
            "explanation": "陶瓷是良好的绝缘体，常用于电气设备的绝缘材料。"
        },
        {
            "question": "以下哪项是不可再生能源？",
            "options": ["风能", "水能", "核能", "太阳能"],
            "answer": 2,
            "category": "能源",
            "explanation": "核能依赖于放射性物质，这些物质是有限的，因此核能属于不可再生能源。"
        },
        {
            "question": "地球公转产生了什么现象？",
            "options": ["四季变化", "昼夜交替", "潮汐", "极光"],
            "answer": 0,
            "category": "地理",
            "explanation": "地球绕太阳公转，由于地轴倾斜，导致太阳直射点在南北回归线之间移动，从而产生四季变化。"
        },
        {
            "question": "以下哪项是人体的主要消化器官？",
            "options": ["心脏", "肺", "胃", "肾脏"],
            "answer": 2,
            "category": "生物",
            "explanation": "胃是人体的主要消化器官之一，负责初步消化食物，尤其是蛋白质。"
        },
        {
            "question": "以下哪项是导体？",
            "options": ["木材", "玻璃", "铁", "橡胶"],
            "answer": 2,
            "category": "物理",
            "explanation": "铁是金属，属于导体，能够导电。木材、玻璃和橡胶都是绝缘体。"
        },
        {
            "question": "以下哪项是太阳系中的矮行星？",
            "options": ["水星", "金星", "冥王星", "火星"],
            "answer": 2,
            "category": "天文",
            "explanation": "冥王星在2006年被重新分类为矮行星，不再被视为太阳系的第八大行星。"
        },
        {
            "question": "以下哪项是简单机械？",
            "options": ["汽车", "飞机", "杠杆", "电脑"],
            "answer": 2,
            "category": "物理",
            "explanation": "杠杆是一种简单机械，由支点、动力臂和阻力臂组成，能够省力或改变力的方向。"
        }
    ]
    
    # 随机打乱题目顺序
    random.shuffle(all_questions)
    
    # 随机选择5道题
    generated_questions = all_questions[:5]
    
    # 为每道题添加唯一ID和随机生成的标识符，确保每次题目不同
    for i, question in enumerate(generated_questions):
        question["id"] = i + 1
        # 添加随机标识符，确保前端能识别到题目变化
        question["quiz_id"] = random.randint(100000, 999999)
    
    return jsonify(generated_questions)

# 用户认证API

# 注册API
@app.route('/api/register', methods=['POST'])
def register():
    try:
        # 获取注册数据
        register_data = request.json
        username = register_data.get('username')
        password = register_data.get('password')
        name = register_data.get('name')
        
        # 验证数据
        if not all([password, name]):
            return jsonify({'status': 'error', 'message': '请填写完整的注册信息'}), 400
        
        # 验证密码是否为6位数字
        if not (password.isdigit() and len(password) == 6):
            return jsonify({'status': 'error', 'message': '密码必须是6位数字'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查名字是否已存在
        cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return jsonify({'status': 'error', 'message': '该名字已被注册'}), 400
        
        # 创建新用户
        username = username or name  # 用户名默认为名字
        cursor.execute('''
            INSERT INTO users (username, password, name, totalScore)
            VALUES (?, ?, ?, ?)
        ''', (username, password, name, 0))
        
        conn.commit()
        new_user_id = cursor.lastrowid
        
        # 获取新创建的用户
        cursor.execute('SELECT * FROM users WHERE id = ?', (new_user_id,))
        new_user = dict(cursor.fetchone())
        conn.close()
        
        return jsonify({'status': 'success', 'message': '注册成功', 'user': new_user}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 登录API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        # 获取登录数据
        login_data = request.json
        username = login_data.get('username')
        password = login_data.get('password')
        
        # 验证数据
        if not all([username, password]):
            return jsonify({'status': 'error', 'message': '请填写完整的登录信息'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查找用户 - 使用用户名或名字登录
        cursor.execute('SELECT * FROM users WHERE (username = ? OR name = ?) AND password = ?', (username, username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({'status': 'success', 'message': '登录成功', 'user': dict(user)}), 200
        else:
            return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取当前用户信息API
@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        # 这里简化处理，实际项目中应该使用token验证
        username = request.args.get('username')
        if not username:
            return jsonify({'status': 'error', 'message': '未提供用户名'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查找用户
        cursor.execute('SELECT * FROM users WHERE username = ? OR name = ?', (username, username))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({'status': 'success', 'user': dict(user)}), 200
        else:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 更新用户积分API
@app.route('/api/update-score', methods=['POST'])
def update_score():
    try:
        # 获取更新数据
        update_data = request.json
        username = update_data.get('username')
        score = update_data.get('score', 0)
        
        # 验证数据
        if not username:
            return jsonify({'status': 'error', 'message': '未提供用户名'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查找用户并更新积分
        cursor.execute('UPDATE users SET totalScore = totalScore + ? WHERE username = ? OR name = ?', (score, username, username))
        
        # 检查是否有行被更新
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 获取更新后的用户数据
        cursor.execute('SELECT * FROM users WHERE username = ? OR name = ?', (username, username))
        user = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '积分更新成功', 'user': dict(user)}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 用户课程权限管理API

# 获取所有用户（用于主机管理）
@app.route('/api/users', methods=['GET'])
def get_all_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取所有用户
        cursor.execute('SELECT id, username, name, totalScore FROM users')
        users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户的课程权限
@app.route('/api/user/<int:user_id>/courses', methods=['GET'])
def get_user_courses(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 获取用户已有的课程权限
        cursor.execute('''
            SELECT cp.chapter_id, c.name 
            FROM user_course_permissions cp
            JOIN chapters c ON cp.chapter_id = c.id
            WHERE cp.user_id = ?
        ''', (user_id,))
        user_courses = [dict(row) for row in cursor.fetchall()]
        
        # 获取所有章节（包括一级和二级，用于权限管理界面）
        cursor.execute('SELECT id, name, level, parent_id FROM chapters ORDER BY level, name')
        all_courses = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({
            'user': dict(user),
            'user_courses': user_courses,
            'all_courses': all_courses
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 更新用户的课程权限
@app.route('/api/user/<int:user_id>/courses', methods=['PUT'])
def update_user_courses(user_id):
    try:
        # 获取更新数据
        update_data = request.json
        course_ids = update_data.get('course_ids', [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证用户是否存在
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 开始事务
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # 删除用户现有的所有课程权限
            cursor.execute('DELETE FROM user_course_permissions WHERE user_id = ?', (user_id,))
            
            # 添加新的课程权限
            for course_id in course_ids:
                cursor.execute('''
                    INSERT INTO user_course_permissions (user_id, chapter_id)
                    VALUES (?, ?)
                ''', (user_id, course_id))
            
            # 提交事务
            conn.commit()
            
            conn.close()
            return jsonify({'status': 'success', 'message': '课程权限更新成功'})
        except Exception as e:
            # 回滚事务
            conn.rollback()
            conn.close()
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户有权限访问的章节
@app.route('/api/user/<int:user_id>/available-chapters', methods=['GET'])
def get_user_available_chapters(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证用户是否存在
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 获取用户有权限的一级章节
        cursor.execute('''
            SELECT c.id, c.name, c.level, c.parent_id
            FROM chapters c
            JOIN user_course_permissions cp ON c.id = cp.chapter_id
            WHERE cp.user_id = ? AND c.level = 1
        ''', (user_id,))
        available_chapters = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(available_chapters)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 运行服务器
if __name__ == '__main__':
    import sys
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='冷湖知识复习系统后端服务器')
    parser.add_argument('--port', type=int, default=8081, help='服务器端口')
    args = parser.parse_args()
    
    init_data()
    app.run(host='0.0.0.0', port=args.port, debug=True)
