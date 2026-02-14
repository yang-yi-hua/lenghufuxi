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
    # 只对API响应添加JSON内容类型
    if request.path.startswith('/api/'):
        response.headers.add('Content-Type', 'application/json; charset=utf-8')
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
            code TEXT,
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
            image TEXT,
            course_code TEXT
        )
    ''')
    
    # 为现有表添加code列（如果不存在）
    try:
        cursor.execute('ALTER TABLE chapters ADD COLUMN code TEXT')
    except:
        pass  # 如果列已存在，忽略错误
    
    # 为现有表添加chapter_id列（如果不存在）
    try:
        cursor.execute('ALTER TABLE knowledge ADD COLUMN chapter_id INTEGER')
        # 添加外键约束（注意：SQLite不支持直接添加外键约束到现有表）
    except:
        pass  # 如果列已存在，忽略错误
    
    # 为现有表添加course_code列（如果不存在）
    try:
        cursor.execute('ALTER TABLE knowledge ADD COLUMN course_code TEXT')
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

# 基于知识点动态生成题目
def generate_questions_from_knowledge_points(knowledge_points):
    import random
    
    if not knowledge_points:
        return []
    
    generated_questions = []
    
    for kp in knowledge_points:
        title = kp.get('title', '')
        content = kp.get('content', '')
        category = kp.get('category', '')
        chapter_id = kp.get('chapter_id')
        
        if not title or not content:
            continue
        
        # 根据知识点内容生成题目
        question = generate_question_from_knowledge(title, content, category, chapter_id)
        if question:
            generated_questions.append(question)
    
    return generated_questions

def generate_question_from_knowledge(title, content, category, chapter_id):
    import random
    
    # 根据知识点内容生成不同类型的题目
    question_templates = {
        '水的三态变化': [
            {
                'question': f'水的三态变化包括哪些状态？',
                'options': ['固态、液态、气态', '固态、液态、等离子态', '液态、气态、等离子态', '固态、气态、等离子态'],
                'answer': 0,
                'explanation': '水有三种状态：固态（冰）、液态（水）、气态（水蒸气）。'
            },
            {
                'question': f'水的三态变化属于什么变化？',
                'options': ['化学变化', '物理变化', '生物变化', '核变化'],
                'answer': 1,
                'explanation': '水的三态变化是物理变化，由温度变化引起。'
            },
            {
                'question': f'水在什么条件下会从液态变成固态？',
                'options': ['温度升高', '温度降低', '压力增大', '压力减小'],
                'answer': 1,
                'explanation': '水在温度降低到0°C以下时会从液态变成固态（冰）。'
            }
        ],
        '哺乳动物特征': [
            {
                'question': f'哺乳动物的主要特征是什么？',
                'options': ['胎生哺乳', '卵生', '冷血', '体表有鳞片'],
                'answer': 0,
                'explanation': '哺乳动物的主要特征包括：胎生、哺乳、体表被毛、体温恒定、心脏四腔。'
            },
            {
                'question': f'以下哪种动物不是哺乳动物？',
                'options': ['狗', '猫', '鸡', '鲸鱼'],
                'answer': 2,
                'explanation': '鸡是鸟类，不是哺乳动物。狗、猫和鲸鱼都是哺乳动物。'
            },
            {
                'question': f'哺乳动物的体温特点是？',
                'options': ['体温恒定', '体温不恒定', '随环境变化', '无法确定'],
                'answer': 0,
                'explanation': '哺乳动物是恒温动物，体温保持恒定。'
            }
        ],
        '光合作用': [
            {
                'question': f'光合作用的主要场所是？',
                'options': ['叶绿体', '线粒体', '细胞核', '细胞质'],
                'answer': 0,
                'explanation': '光合作用是植物利用光能将二氧化碳和水转化为有机物并释放氧气的过程，主要场所是叶绿体。'
            },
            {
                'question': f'光合作用的原料是什么？',
                'options': ['氧气和水', '二氧化碳和水', '氧气和二氧化碳', '水和无机盐'],
                'answer': 1,
                'explanation': '光合作用的原料是二氧化碳和水，产物是有机物和氧气。'
            },
            {
                'question': f'光合作用需要什么条件？',
                'options': ['光照', '黑暗', '低温', '高压'],
                'answer': 0,
                'explanation': '光合作用需要光照作为能量来源。'
            }
        ],
        '简单机械': [
            {
                'question': f'以下哪项不属于简单机械？',
                'options': ['杠杆', '滑轮', '蒸汽机', '斜面'],
                'answer': 2,
                'explanation': '简单机械包括：杠杆、滑轮、轮轴、斜面、楔、螺旋。蒸汽机是一种复杂的热机，不属于简单机械。'
            },
            {
                'question': f'杠杆的支点是指？',
                'options': ['杠杆的固定点', '杠杆的受力点', '杠杆的作用点', '杠杆的重心'],
                'answer': 0,
                'explanation': '杠杆的支点是杠杆绕着转动的固定点。'
            },
            {
                'question': f'斜面的作用是？',
                'options': ['省力', '费力', '不省力也不费力', '以上都不对'],
                'answer': 0,
                'explanation': '斜面可以省力，但需要移动更长的距离。'
            }
        ],
        '声音传播介质': [
            {
                'question': f'声音不能在以下哪种介质中传播？',
                'options': ['空气', '水', '真空', '金属'],
                'answer': 2,
                'explanation': '声音需要介质传播，介质密度越大，传播速度越快。声音不能在真空中传播，因为真空中没有物质粒子来传递声波。'
            },
            {
                'question': f'声音在以下哪种介质中传播速度最快？',
                'options': ['空气', '水', '钢铁', '真空'],
                'answer': 2,
                'explanation': '声音在固体中传播速度最快，在液体中次之，在气体中最慢。声音不能在真空中传播。'
            }
        ],
        '导体与绝缘体': [
            {
                'question': f'以下哪种物质是导体？',
                'options': ['塑料', '橡胶', '铜', '玻璃'],
                'answer': 2,
                'explanation': '铜是导体，塑料、橡胶和玻璃是绝缘体。'
            },
            {
                'question': f'以下哪种物质是绝缘体？',
                'options': ['铜', '铝', '塑料', '铁'],
                'answer': 2,
                'explanation': '塑料是绝缘体，铜、铝和铁是导体。'
            }
        ],
        '地球自转': [
            {
                'question': f'地球自转产生了什么现象？',
                'options': ['四季变化', '昼夜交替', '潮汐', '极光'],
                'answer': 1,
                'explanation': '地球自西向东自转，周期约为24小时，产生昼夜交替现象。四季变化是由地球公转引起的，潮汐是由月球和太阳的引力引起的，极光是由太阳活动引起的。'
            },
            {
                'question': f'地球自转的方向是？',
                'options': ['自东向西', '自西向东', '自北向南', '自南向北'],
                'answer': 1,
                'explanation': '地球自西向东自转，周期约为24小时，产生昼夜交替现象。'
            }
        ],
        '可再生能源': [
            {
                'question': f'以下哪种能源是可再生能源？',
                'options': ['煤炭', '石油', '太阳能', '天然气'],
                'answer': 2,
                'explanation': '太阳能是可再生能源，煤炭、石油和天然气是不可再生能源。'
            },
            {
                'question': f'可再生能源的特点是？',
                'options': ['会耗尽', '可以不断再生', '污染环境', '成本高'],
                'answer': 1,
                'explanation': '可再生能源是可以不断再生的能源，如太阳能、风能、水能、生物质能等。'
            }
        ],
        '呼吸系统': [
            {
                'question': f'人体呼吸系统包括什么？',
                'options': ['鼻腔和喉咙', '呼吸道和肺', '气管和肺', '鼻腔和肺'],
                'answer': 1,
                'explanation': '人体呼吸系统包括呼吸道和肺，肺是气体交换的主要场所。'
            },
            {
                'question': f'人体气体交换的主要场所是？',
                'options': ['鼻腔', '喉咙', '肺', '气管'],
                'answer': 2,
                'explanation': '人体呼吸系统包括呼吸道和肺，肺是气体交换的主要场所。鼻腔、喉咙和气管是呼吸道的组成部分，主要作用是过滤、温暖和湿润空气。'
            }
        ],
        '伯努利原理': [
            {
                'question': f'伯努利原理描述的是？',
                'options': ['空气流速大的地方压强大', '空气流速大的地方压强小', '空气流速与压强无关', '空气流速小的地方压强小'],
                'answer': 1,
                'explanation': '伯努利原理指出：流体流速大的地方压强小，流速小的地方压强大。'
            },
            {
                'question': f'根据伯努利原理，飞机机翼产生升力的原因是？',
                'options': ['机翼上方空气流速大，压强小', '机翼上方空气流速小，压强大', '机翼下方空气流速大，压强小', '机翼下方空气流速小，压强大'],
                'answer': 0,
                'explanation': '根据伯努利原理，飞机机翼上表面弯曲，空气流速大，压强小；下表面平坦，空气流速小，压强大，产生向上的升力。'
            }
        ],
        '鸟为什么会飞': [
            {
                'question': f'鸟的翅膀形状有利于飞行，这是因为？',
                'options': ['翅膀面积大', '翅膀上表面弯曲，下表面平坦', '翅膀重量轻', '翅膀有羽毛'],
                'answer': 1,
                'explanation': '鸟的翅膀上表面弯曲，下表面平坦，使得上表面空气流速大，压强小，下表面空气流速小，压强大，产生向上的升力。'
            },
            {
                'question': f'鸟飞行时，翅膀上方的空气流速？',
                'options': ['比下方大', '比下方小', '与下方相同', '无法确定'],
                'answer': 0,
                'explanation': '鸟飞行时，翅膀上方的空气流速比下方大，因为上表面弯曲，空气需要经过更长的距离。'
            }
        ],
        '声音的三要素': [
            {
                'question': f'声音的三要素不包括？',
                'options': ['响度', '音调', '音色', '频率'],
                'answer': 3,
                'explanation': '声音的三要素是响度、音调和音色。频率是影响音调的因素，不是声音的三要素之一。'
            },
            {
                'question': f'以下哪项不是声音的三要素？',
                'options': ['响度', '音调', '音色', '振幅'],
                'answer': 3,
                'explanation': '声音的三要素是响度、音调和音色。振幅是影响响度的因素，不是声音的三要素之一。'
            }
        ],
        '影响声音响度的因素': [
            {
                'question': f'影响声音响度的因素是？',
                'options': ['频率', '振幅', '介质', '温度'],
                'answer': 1,
                'explanation': '影响声音响度的因素是振幅，振幅越大，响度越大。'
            },
            {
                'question': f'以下哪种情况声音响度最大？',
                'options': ['振幅小', '振幅大', '频率高', '频率低'],
                'answer': 1,
                'explanation': '振幅越大，响度越大。'
            }
        ],
        '影响声音音调的因素': [
            {
                'question': f'影响声音音调的因素是？',
                'options': ['振幅', '频率', '介质', '温度'],
                'answer': 1,
                'explanation': '影响声音音调的因素是频率，频率越高，音调越高。'
            },
            {
                'question': f'以下哪种情况声音音调最高？',
                'options': ['频率低', '频率高', '振幅小', '振幅大'],
                'answer': 1,
                'explanation': '频率越高，音调越高。'
            }
        ],
        '影响声音音色的因素': [
            {
                'question': f'影响声音音色的因素是？',
                'options': ['振幅', '频率', '发声体的材料和结构', '介质'],
                'answer': 2,
                'explanation': '影响声音音色的因素是发声体的材料和结构。'
            },
            {
                'question': f'不同乐器演奏同一首曲子，我们能分辨出来是因为？',
                'options': ['响度不同', '音调不同', '音色不同', '频率不同'],
                'answer': 2,
                'explanation': '不同乐器的音色不同，我们能通过音色分辨不同的乐器。'
            }
        ],
        '声音传播需要介质': [
            {
                'question': f'声音传播需要什么？',
                'options': ['真空', '介质', '电力', '磁力'],
                'answer': 1,
                'explanation': '声音传播需要介质，介质可以是固体、液体或气体。'
            },
            {
                'question': f'为什么声音不能在真空中传播？',
                'options': ['真空温度太低', '真空没有介质', '真空压力太大', '真空没有光线'],
                'answer': 1,
                'explanation': '声音传播需要介质，真空中没有物质粒子来传递声波，所以声音不能在真空中传播。'
            }
        ],
        '声音在不同介质中的传播速度': [
            {
                'question': f'声音在以下哪种介质中传播速度最快？',
                'options': ['空气', '水', '钢铁', '真空'],
                'answer': 2,
                'explanation': '声音在固体中传播速度最快，在液体中次之，在气体中最慢。声音不能在真空中传播。'
            },
            {
                'question': f'声音在以下哪种介质中传播速度最慢？',
                'options': ['钢铁', '水', '空气', '以上都不对'],
                'answer': 2,
                'explanation': '声音在气体中传播速度最慢，在液体中次之，在固体中最快。'
            }
        ]
    }
    
    # 根据知识点标题获取对应的题目模板
    templates = question_templates.get(title, [])
    
    if not templates:
        # 如果没有找到对应的模板，根据知识点内容生成通用题目
        return generate_generic_question(title, content, category, chapter_id)
    
    # 随机选择一个题目模板
    template = random.choice(templates)
    
    # 创建题目对象
    question = {
        'question': template['question'],
        'options': template['options'].copy(),
        'answer': template['answer'],
        'category': category,
        'course_id': chapter_id if chapter_id else 1,
        'explanation': template['explanation']
    }
    
    # 随机打乱选项顺序
    original_options = question['options'].copy()
    original_answer = question['answer']
    
    option_indices = list(range(len(original_options)))
    random.shuffle(option_indices)
    
    question['options'] = [original_options[idx] for idx in option_indices]
    question['answer'] = option_indices.index(original_answer)
    
    return question

def generate_generic_question(title, content, category, chapter_id):
    import random
    
    # 根据知识点内容生成通用题目
    sentences = content.split('。')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return None
    
    # 选择一个句子作为题目基础
    base_sentence = random.choice(sentences)
    
    # 生成选择题
    question = {
        'question': f'关于{title}，以下说法正确的是？',
        'options': [base_sentence, '这是一个错误的选项1', '这是一个错误的选项2', '这是一个错误的选项3'],
        'answer': 0,
        'category': category,
        'course_id': chapter_id if chapter_id else 1,
        'explanation': f'{title}：{content}'
    }
    
    # 随机打乱选项顺序
    original_options = question['options'].copy()
    original_answer = question['answer']
    
    option_indices = list(range(len(original_options)))
    random.shuffle(option_indices)
    
    question['options'] = [original_options[idx] for idx in option_indices]
    question['answer'] = option_indices.index(original_answer)
    
    return question

# 加载数据（保留，用于兼容旧数据）
def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# 保存数据（保留，用于兼容旧数据）
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 根路径返回quiz-system-updated.html
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'quiz-system-updated.html')

# 访问quiz-system-updated.html
@app.route('/quiz-system-updated.html')
def quiz_system():
    return send_from_directory(BASE_DIR, 'quiz-system-updated.html')

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

# quiz样式文件
@app.route('/quiz-style.css')
def quiz_style():
    return serve_file('quiz-style.css')

# JavaScript文件
@app.route('/script.js')
def script():
    return serve_file('script.js')

# quiz JavaScript文件
@app.route('/quiz-script.js')
def quiz_script():
    return serve_file('quiz-script.js')

# 题库文件
@app.route('/science-questions.json')
def questions_file():
    return serve_file('science-questions.json')

# 编辑知识点页面
@app.route('/edit-knowledge.html')
def edit_knowledge_page():
    return serve_file('edit-knowledge.html')

# 音效文件服务
@app.route('/shengyin/<path:filename>')
def serve_audio(filename):
    audio_dir = os.path.join(BASE_DIR, 'shengyin')
    if os.path.exists(audio_dir):
        return send_from_directory(audio_dir, filename)
    return f"Audio directory not found", 404

# 获取排行榜
@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从用户表中获取排名数据，只显示有积分且名称正常的用户
    cursor.execute('''
        SELECT name, totalScore as score, 0 as correctCount, 0 as time, datetime('now') as date
        FROM users
        WHERE totalScore > 0 AND name NOT LIKE '%?%' AND name NOT LIKE '%鍖%' AND name NOT LIKE '%鏉%'
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
    
    # 获取查询参数
    course_code = request.args.get('course_code')
    chapter_id = request.args.get('chapter_id')
    
    # 根据参数筛选知识点
    if course_code:
        cursor.execute('SELECT * FROM knowledge WHERE course_code = ?', (course_code,))
    elif chapter_id:
        cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (chapter_id,))
    else:
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
    
    try:
        # 获取新知识点数据
        new_knowledge = request.json
        chapter_id = new_knowledge.get('chapter_id')
        course_code = None
        
        # 如果指定了章节，获取章节的标识码
        if chapter_id:
            cursor.execute('SELECT code FROM chapters WHERE id = ?', (chapter_id,))
            chapter = cursor.fetchone()
            if chapter:
                course_code = chapter[0]
        
        # 插入知识点
        cursor.execute('''
            INSERT INTO knowledge (title, content, category, image, chapter_id, course_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_knowledge['title'], new_knowledge['content'], new_knowledge['category'], new_knowledge.get('image', ''), chapter_id, course_code))
        
        conn.commit()
        new_knowledge_id = cursor.lastrowid
        
        # 获取新创建的知识点
        cursor.execute('SELECT * FROM knowledge WHERE id = ?', (new_knowledge_id,))
        created_knowledge = dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify(created_knowledge), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# 更新知识点
@app.route('/api/knowledge/<int:knowledge_id>', methods=['PUT'])
def update_knowledge(knowledge_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取更新数据
        updated_data = request.json
        chapter_id = updated_data.get('chapter_id')
        course_code = None
        
        # 如果指定了章节，获取章节的标识码
        if chapter_id:
            cursor.execute('SELECT code FROM chapters WHERE id = ?', (chapter_id,))
            chapter = cursor.fetchone()
            if chapter:
                course_code = chapter[0]
        
        # 更新知识点
        cursor.execute('''
            UPDATE knowledge SET title = ?, content = ?, category = ?, image = ?, chapter_id = ?, course_code = ?
            WHERE id = ?
        ''', (updated_data['title'], updated_data['content'], updated_data['category'], updated_data.get('image', ''), chapter_id, course_code, knowledge_id))
        
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
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

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
    
    # 生成标识码：所有字首字母大写
    chapter_name = new_chapter['name']
    # 分割名称为单词，取每个单词的首字母大写
    words = chapter_name.split()
    code = ''.join(word[0].upper() for word in words if word)
    
    # 插入章节
    cursor.execute('''
        INSERT INTO chapters (name, code, level, parent_id)
        VALUES (?, ?, ?, ?)
    ''', (new_chapter['name'], code, new_chapter['level'], new_chapter.get('parent_id')))
    
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
    
    # 生成标识码：所有字首字母大写
    chapter_name = updated_data['name']
    # 分割名称为单词，取每个单词的首字母大写
    words = chapter_name.split()
    code = ''.join(word[0].upper() for word in words if word)
    
    # 更新章节
    cursor.execute('''
        UPDATE chapters SET name = ?, code = ?, level = ?, parent_id = ?
        WHERE id = ?
    ''', (updated_data['name'], code, updated_data['level'], updated_data.get('parent_id'), chapter_id))
    
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
    
    # 每次都使用当前时间作为随机种子，确保每次生成的题目都是真正随机的
    random.seed(time.time())
    
    # 获取请求参数
    request_params = request.json
    chapter_id = request_params.get('chapter_id')
    first_level_id = request_params.get('first_level_id')
    second_level_id = request_params.get('second_level_id')
    question_count = request_params.get('count', 5)  # 获取请求的题目数量，默认5道
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 从数据库获取知识点
    if chapter_id:
        # 如果是科学课程（chapter_id = 1），获取所有知识点
        if chapter_id == 1:
            cursor.execute('SELECT * FROM knowledge')
        else:
            # 按指定章节获取知识点
            cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (chapter_id,))
    elif second_level_id:
        # 如果是科学课程（second_level_id = 1），获取所有知识点
        if second_level_id == 1:
            cursor.execute('SELECT * FROM knowledge')
        else:
            # 按第二级章节获取知识点
            cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (second_level_id,))
    elif first_level_id:
        # 如果是科学课程（first_level_id = 1），获取所有知识点
        if first_level_id == 1:
            cursor.execute('SELECT * FROM knowledge')
        else:
            # 按第一级章节获取知识点（包括其下的第二级章节）
            # 先获取第一级章节下的所有第二级章节
            cursor.execute('SELECT id FROM chapters WHERE parent_id = ?', (first_level_id,))
            sub_chapters = cursor.fetchall()
            sub_chapter_ids = [sub_chapter[0] for sub_chapter in sub_chapters]
            
            # 构建查询，包括第一级章节和其下的第二级章节
            if sub_chapter_ids:
                placeholders = ','.join(['?'] * len(sub_chapter_ids))
                query = f'SELECT * FROM knowledge WHERE chapter_id = ? OR chapter_id IN ({placeholders})'
                cursor.execute(query, [first_level_id] + sub_chapter_ids)
            else:
                # 如果没有第二级章节，只查询第一级章节
                cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (first_level_id,))
    else:
        # 获取所有知识点
        cursor.execute('SELECT * FROM knowledge')
    
    knowledge_points = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 根据知识点动态生成题目
    all_questions = generate_questions_from_knowledge_points(knowledge_points)
    
    # 根据课程ID筛选相关题目
    selected_course_id = None
    if chapter_id:
        selected_course_id = chapter_id
    elif second_level_id:
        selected_course_id = second_level_id
    elif first_level_id:
        selected_course_id = first_level_id
    
    # 筛选与所选课程相关的题目
    if selected_course_id:
        course_related_questions = []
        for question in all_questions:
            if question.get('course_id') == selected_course_id:
                course_related_questions.append(question)
        
        # 如果有相关题目，使用相关题目
        if course_related_questions:
            all_questions = course_related_questions
        else:
            # 如果没有相关题目，返回空列表
            all_questions = []
    else:
        # 如果没有选择课程，根据知识点筛选相关题目
        if knowledge_points:
            # 提取知识点的类别
            categories = set([kp['category'] for kp in knowledge_points if kp.get('category')])
            
            # 筛选与知识点类别相关的题目
            relevant_questions = []
            for question in all_questions:
                if question['category'] in categories:
                    relevant_questions.append(question)
            
            # 如果有相关题目，使用相关题目
            if relevant_questions:
                all_questions = relevant_questions
    
    # 确保返回指定数量的题目，每次都使用不同的随机算法
    generated_questions = []
    
    # 如果题目数量足够，直接随机选择指定数量的题目
    if len(all_questions) >= question_count:
        # 随机打乱题目顺序
        random.shuffle(all_questions)
        # 选择前question_count道题
        generated_questions = all_questions[:question_count]
    else:
        # 如果题目数量不足，使用所有可用题目
        generated_questions = all_questions.copy()
    
    # 为每道题添加唯一ID和随机生成的标识符，确保每次题目不同
    # 同时随机打乱选项顺序，并调整正确答案索引
    for i, question in enumerate(generated_questions):
        question["id"] = i + 1
        # 添加随机标识符，确保前端能识别到题目变化
        question["quiz_id"] = random.randint(100000, 999999)
        
        # 随机打乱选项顺序
        original_options = question["options"].copy()
        original_answer = question["answer"]
        
        # 创建选项索引列表
        option_indices = list(range(len(original_options)))
        # 随机打乱索引
        random.shuffle(option_indices)
        
        # 根据打乱的索引重新排列选项
        question["options"] = [original_options[idx] for idx in option_indices]
        
        # 找到正确答案在新选项中的位置
        question["answer"] = option_indices.index(original_answer)
    
    return jsonify(generated_questions)

# 按章节生成题目
@app.route('/api/generate-questions-by-chapter', methods=['POST'])
def generate_questions_by_chapter():
    data = request.get_json()
    chapter_id = data.get('chapter_id')
    question_count = data.get('question_count', 10)
    
    # 连接数据库
    conn = sqlite3.connect('quiz_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查询章节的知识点
    cursor.execute('''
        SELECT k.* FROM knowledge k
        WHERE k.chapter_id = ?
    ''', (chapter_id,))
    
    knowledge_points = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 根据知识点动态生成题目
    all_questions = generate_questions_from_knowledge_points(knowledge_points)
    
    # 确保返回指定数量的题目
    if len(all_questions) > question_count:
        random.shuffle(all_questions)
        all_questions = all_questions[:question_count]
    
    # 为每道题添加唯一ID和随机生成的标识符
    for i, question in enumerate(all_questions):
        question["id"] = i + 1
        question["quiz_id"] = random.randint(100000, 999999)
        
        # 随机打乱选项顺序
        original_options = question["options"].copy()
        original_answer = question["answer"]
        
        option_indices = list(range(len(original_options)))
        random.shuffle(option_indices)
        
        question["options"] = [original_options[idx] for idx in option_indices]
        question["answer"] = option_indices.index(original_answer)
    
    return jsonify(all_questions)

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

# 用户答题时间管理API

# 记录用户开始答题时间
@app.route('/api/user/<int:user_id>/quiz-time/<int:chapter_id>', methods=['POST'])
def record_quiz_time(user_id, chapter_id):
    try:
        import datetime
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取请求参数
        request_data = request.json
        interval_days = request_data.get('interval_days', 0)
        
        # 获取当前时间
        now = datetime.datetime.now()
        last_quiz_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算下次可答题时间
        if interval_days > 0:
            next_available = now + datetime.timedelta(days=interval_days)
            next_available_time = next_available.strftime('%Y-%m-%d %H:%M:%S')
        else:
            next_available_time = last_quiz_time
        
        # 插入或更新答题时间记录
        cursor.execute('''
            INSERT OR REPLACE INTO user_quiz_times 
            (user_id, chapter_id, last_quiz_time, next_available_time, interval_days)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, chapter_id, last_quiz_time, next_available_time, interval_days))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '答题时间记录成功',
            'last_quiz_time': last_quiz_time,
            'next_available_time': next_available_time,
            'interval_days': interval_days
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户的答题时间记录
@app.route('/api/user/<int:user_id>/quiz-times', methods=['GET'])
def get_user_quiz_times(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户的所有答题时间记录
        cursor.execute('''
            SELECT qt.*, c.name as chapter_name
            FROM user_quiz_times qt
            JOIN chapters c ON qt.chapter_id = c.id
            WHERE qt.user_id = ?
        ''', (user_id,))
        quiz_times = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(quiz_times)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 检查用户是否可以开始答题
@app.route('/api/user/<int:user_id>/can-quiz/<int:chapter_id>', methods=['GET'])
def check_can_quiz(user_id, chapter_id):
    try:
        import datetime
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户的答题时间记录
        cursor.execute('''
            SELECT * FROM user_quiz_times 
            WHERE user_id = ? AND chapter_id = ?
        ''', (user_id, chapter_id))
        record = cursor.fetchone()
        
        conn.close()
        
        can_quiz = True
        next_available_time = None
        remaining_time = 0
        
        if record:
            # 检查是否到了下次可答题时间
            now = datetime.datetime.now()
            next_available = datetime.datetime.strptime(record['next_available_time'], '%Y-%m-%d %H:%M:%S')
            
            if now < next_available:
                can_quiz = False
                next_available_time = record['next_available_time']
                remaining_time = int((next_available - now).total_seconds())
        
        return jsonify({
            'can_quiz': can_quiz,
            'next_available_time': next_available_time,
            'remaining_time': remaining_time
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 运行服务器
if __name__ == '__main__':
    import sys
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='冷湖知识复习系统后端服务器')
    parser.add_argument('--port', type=int, default=9000, help='服务器端口')
    args = parser.parse_args()
    
    init_data()
    app.run(host='0.0.0.0', port=args.port, debug=True)
