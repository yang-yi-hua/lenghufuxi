from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import sqlite3
import random
from datetime import datetime

# 获取当前目录的绝对路径
BASE_DIR = os.path.abspath('.')

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lenghu_quiz_secret_key_2024'

# 创建SocketIO实例
socketio = SocketIO(app, cors_allowed_origins='*')

# 在线用户跟踪
online_users = {}  # {user_id: {name: str, totalScore: int, sid: str}}

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
            cursor.execute('INSERT INTO chapters (name, code, level, parent_id) VALUES (?, ?, ?, ?)',
                       (chapter['name'], chapter['name'], chapter['level'], None))
    
    # 插入默认的第二级章节（科学）
    cursor.execute('SELECT id FROM chapters WHERE name = ? AND level = 1', ('科学',))
    science_chapter = cursor.fetchone()
    if science_chapter:
        science_id = science_chapter[0]
        cursor.execute('SELECT COUNT(*) FROM chapters WHERE parent_id = ?', (science_id,))
        if cursor.fetchone()[0] == 0:
            default_subchapters = [
                {'name': '基础科学', 'code': 'SC-001'},
                {'name': '物理知识', 'code': 'SC-002'},
                {'name': '化学知识', 'code': 'SC-003'},
                {'name': '生物知识', 'code': 'SC-004'}
            ]
            for subchapter in default_subchapters:
                cursor.execute('INSERT INTO chapters (name, code, level, parent_id) VALUES (?, ?, ?, ?)',
                           (subchapter['name'], subchapter['code'], 2, science_id))
    
    conn.commit()
    conn.close()

# 初始化数据库
init_database()

# 基于知识点动态生成题目
def generate_questions_from_knowledge_points(knowledge_points):
    import random
    
    # 为不同类型的知识点准备具体的错误选项模板（与知识点高度相关但错误）
    error_templates = {
        '物理': {
            '声音': [
                '声音在真空中传播速度最快',
                '声音的传播需要介质，但介质越稀薄传播越快',
                '声音在固体中的传播速度比在空气中慢',
                '声音的响度只与声源的振幅有关，与距离无关'
            ],
            '力': [
                '力可以脱离物体而独立存在',
                '力的三要素是大小、方向和作用点，但方向不影响力的作用效果',
                '相互接触的两个物体之间一定有力的作用',
                '物体受力运动，不受力静止'
            ],
            '光': [
                '光在同种均匀介质中沿直线传播，但在水中会弯曲',
                '光的传播速度是3×10⁸m/s，在任何介质中都相同',
                '光从空气斜射入水中时，折射角大于入射角',
                '平面镜成像是实像，像与物大小相等'
            ],
            '电': [
                '电流方向与电子定向移动方向相同',
                '串联电路中各用电器两端的电压一定相等',
                '并联电路中各支路的电流一定相等',
                '导体的电阻与电压和电流有关'
            ],
            '热': [
                '物体温度越高，内能越大，热量越多',
                '热传递的实质是温度的传递',
                '比热容大的物体吸收的热量一定多',
                '水的沸点一定是100℃'
            ],
            '机械': [
                '使用任何机械都能省力',
                '机械效率越高，做的有用功越多',
                '功率越大，做功越快，做的功也越多',
                '动能和势能可以相互转化，但总能量会减少'
            ],
            '默认': [
                '该现象只存在于地球表面',
                '该原理与温度变化无关',
                '该过程不需要任何能量参与',
                '该现象在真空中无法发生'
            ]
        },
        '化学': {
            '物质': [
                '混合物是由不同种分子构成的纯净物',
                '化合物是由同种元素组成的纯净物',
                '单质是由不同种元素组成的纯净物',
                '氧化物是由两种元素组成的化合物，其中一种是氧元素'
            ],
            '反应': [
                '化合反应一定是氧化反应',
                '分解反应的生成物一定有单质',
                '置换反应一定有金属单质参加',
                '复分解反应一定有沉淀、气体或水生成'
            ],
            '溶液': [
                '饱和溶液一定是浓溶液，不饱和溶液一定是稀溶液',
                '溶液是均一、稳定、无色透明的液体',
                '溶解度随温度升高而增大的物质，其饱和溶液降温后一定有晶体析出',
                '溶液的质量等于溶质质量加上溶剂质量'
            ],
            '酸碱盐': [
                '酸溶液一定显酸性，碱性溶液一定是碱溶液',
                'pH=7的溶液一定是中性溶液',
                '酸碱中和反应的产物一定是盐和水',
                '盐溶液一定显中性'
            ],
            '默认': [
                '该反应在任何条件下都能进行',
                '该物质在任何溶剂中都能溶解',
                '该过程不需要催化剂参与',
                '该现象与压强变化无关'
            ]
        },
        '生物': {
            '细胞': [
                '所有细胞都有细胞壁、细胞膜、细胞质和细胞核',
                '植物细胞都有叶绿体，能进行光合作用',
                '动物细胞都有中心体，参与细胞分裂',
                '细胞核是遗传信息库，遗传信息主要存在于细胞质中'
            ],
            '新陈代谢': [
                '光合作用只在白天进行，呼吸作用只在晚上进行',
                '光合作用和呼吸作用的原料和产物完全相同',
                '植物只能进行光合作用，动物只能进行呼吸作用',
                '新陈代谢是生物体与外界环境进行物质和能量交换的过程，不需要酶参与'
            ],
            '遗传': [
                '基因位于DNA上，DNA位于染色体上，染色体位于细胞核中',
                '生物的性状都是由基因决定的，与环境无关',
                '显性基因控制的性状一定能表现出来',
                '隐性基因控制的性状永远不能表现出来'
            ],
            '生态': [
                '生态系统中，生产者、消费者、分解者缺一不可',
                '食物链越长，能量损失越多，最高级消费者获得的能量越多',
                '生态系统具有一定的自我调节能力，但这种能力是无限的',
                '生物圈是最大的生态系统，包括地球上所有的生物及其生存环境'
            ],
            '默认': [
                '该生物过程在任何温度下都能进行',
                '该现象与光照强度无关',
                '该过程不需要水分参与',
                '该生物特征在所有物种中都相同'
            ]
        },
        '地理': {
            '地球': [
                '地球是一个正球体，赤道半径与极半径相等',
                '地球自转产生昼夜长短变化，公转产生昼夜交替',
                '地球自西向东自转，从北极上空看是顺时针方向',
                '地球公转轨道是正圆形，公转速度恒定不变'
            ],
            '气候': [
                '纬度越高，气温越低，降水越多',
                '沿海地区降水多，内陆地区降水少',
                '山地迎风坡降水多，背风坡降水少',
                '气候是短时间内的大气状况，天气是长期的平均状况'
            ],
            '地形': [
                '平原海拔一般在200米以下，地面平坦开阔',
                '高原海拔一般在500米以上，地面起伏很大',
                '山地海拔一般在500米以上，坡度较陡，沟谷较深',
                '盆地四周高，中间低，但内部一定是平原'
            ],
            '人口': [
                '人口自然增长率等于出生率减去死亡率',
                '人口密度越大，人口分布越均匀',
                '发达国家人口增长快，发展中国家人口增长慢',
                '人口迁移的主要原因是经济因素'
            ],
            '默认': [
                '该地理现象在任何纬度都相同',
                '该地形特征与板块运动无关',
                '该气候类型不受海洋影响',
                '该地区的人口分布与地形无关'
            ]
        },
        '能源': {
            '传统能源': [
                '煤炭是不可再生能源，但燃烧不产生任何污染物',
                '石油是可再生能源，储量丰富，取之不尽',
                '天然气燃烧产物只有二氧化碳，对环境无污染',
                '化石能源的利用不会导致温室效应'
            ],
            '新能源': [
                '太阳能是可再生能源，但只能在白天使用',
                '风能是可再生能源，但发电成本很高',
                '核能是可再生能源，但核废料处理困难',
                '生物质能是可再生能源，但燃烧会产生大量污染物'
            ],
            '节能': [
                '提高能源利用效率就是减少能源消耗',
                '节约能源就是减少能源浪费，不影响生活质量',
                '开发新能源比节约能源更重要',
                '能源危机可以通过开发新能源完全解决'
            ],
            '默认': [
                '该能源在任何地区都能开发利用',
                '该能源技术已经完全成熟',
                '该能源的使用不会对环境造成任何影响',
                '该能源的储量是无限的'
            ]
        },
        '机械': {
            '简单机械': [
                '杠杆一定省力，省力杠杆的动力臂小于阻力臂',
                '定滑轮可以省力，动滑轮可以改变力的方向',
                '滑轮组既能省力又能改变力的方向，但机械效率很低',
                '斜面越陡，越省力，但机械效率越高'
            ],
            '功和能': [
                '做功越多，功率越大',
                '功率越大，做功越多',
                '机械效率越高，做的有用功越多',
                '动能和势能可以相互转化，总能量保持不变'
            ],
            '压强': [
                '压强越大，压力越大',
                '压力越大，压强越大',
                '液体压强与液体密度和深度有关，与容器形状无关',
                '大气压随高度增加而增大'
            ],
            '浮力': [
                '浮力大小与物体浸入液体的深度有关',
                '物体漂浮时受到的浮力大于物体沉底时受到的浮力',
                '密度大的物体受到的浮力大，密度小的物体受到的浮力小',
                '物体受到的浮力方向总是竖直向上'
            ],
            '默认': [
                '该机械原理在任何条件下都适用',
                '该机械效率可以达到100%',
                '该机械的使用不需要任何能量输入',
                '该机械的设计与材料无关'
            ]
        },
        '默认': {
            '通用': [
                '该现象在任何条件下都会发生',
                '该原理只适用于特定环境',
                '该过程不需要任何条件支持',
                '该结果不受任何因素影响'
            ]
        }
    }
    
    # 参考网上常见的题目类型模板
    question_templates = [
        # 概念理解型
        {
            'pattern': '以下关于"{title}"的说法，正确的是：',
            'type': 'concept'
        },
        # 特征描述型
        {
            'pattern': '"{title}"的主要特征不包括：',
            'type': 'feature'
        },
        # 应用判断型
        {
            'pattern': '下列现象中，与"{title}"无关的是：',
            'type': 'application'
        },
        # 原因分析型
        {
            'pattern': '"{title}"产生的主要原因是：',
            'type': 'reason'
        },
        # 区别比较型
        {
            'pattern': '与其他选项相比，"{title}"的独特之处在于：',
            'type': 'comparison'
        },
        # 影响因素型
        {
            'pattern': '影响"{title}"的因素不包括：',
            'type': 'factor'
        },
        # 实例识别型
        {
            'pattern': '下列实例中，属于"{title}"应用的是：',
            'type': 'example'
        },
        # 原理说明型
        {
            'pattern': '"{title}"的工作原理是：',
            'type': 'principle'
        }
    ]
    
    # 为不同类型的题目准备具体的选项模板
    option_templates = {
        '物理': {
            'application': [
                '苹果落地',
                '气球上升',
                '汽车刹车',
                '钢笔吸水'
            ],
            'example': [
                '使用杠杆撬动石头',
                '利用滑轮提升重物',
                '乘坐电梯上楼',
                '用斜面搬运货物'
            ]
        },
        '化学': {
            'application': [
                '铁生锈',
                '食物腐败',
                '酒精挥发',
                '蜡烛燃烧'
            ],
            'example': [
                '实验室制取氧气',
                '工业炼铁',
                '光合作用',
                '海水淡化'
            ]
        },
        '生物': {
            'application': [
                '植物向光生长',
                '人体出汗',
                '种子萌发',
                '候鸟迁徙'
            ],
            'example': [
                '试管婴儿技术',
                '转基因作物',
                '克隆技术',
                '人工授粉'
            ]
        },
        '地理': {
            'application': [
                '四季更替',
                '昼夜长短变化',
                '潮汐现象',
                '极光形成'
            ],
            'example': [
                '修建梯田',
                '南水北调',
                '三北防护林',
                '西气东输'
            ]
        },
        '能源': {
            'application': [
                '太阳能热水器',
                '风力发电站',
                '核电站',
                '火力发电厂'
            ],
            'example': [
                '使用太阳能路灯',
                '安装家用光伏板',
                '推广电动汽车',
                '建设水电站'
            ]
        },
        '机械': {
            'application': [
                '使用螺丝刀拧螺丝',
                '用剪刀剪东西',
                '骑自行车上坡',
                '用锤子敲钉子'
            ],
            'example': [
                '塔吊吊运重物',
                '自行车链条传动',
                '汽车方向盘控制',
                '电梯升降系统'
            ]
        }
    }
    
    questions = []
    for kp in knowledge_points:
        # 获取适合当前知识点类别的错误选项
        category = kp.get('category', '默认')
        category_errors = error_templates.get(category, error_templates['默认'])
        
        # 根据知识点标题选择相关的错误选项
        title = kp['title'].lower()
        suitable_errors = []
        
        # 尝试匹配具体主题
        if isinstance(category_errors, dict):
            for theme, errors in category_errors.items():
                if theme != '默认' and theme in title:
                    suitable_errors = errors
                    break
            
            # 如果没有匹配到具体主题，使用通用错误选项
            if not suitable_errors:
                suitable_errors = category_errors.get('默认', [])
        else:
            suitable_errors = category_errors
        
        # 为每个知识点生成多个不同类型的题目
        for i in range(min(3, len(question_templates))):
            # 随机选择一个题目模板
            template = random.choice(question_templates)
            question_type = template['type']
            
            # 生成题目文本
            question_text = template['pattern'].format(title=kp['title'])
            
            # 生成正确选项
            correct_option = kp['content'][:60] + ('...' if len(kp['content']) > 60 else '')
            
            # 生成错误选项
            unique_errors = []
            temp_errors = suitable_errors.copy()
            random.shuffle(temp_errors)
            
            # 根据题目类型生成不同的错误选项
            if question_type in ['application', 'example'] and category in option_templates:
                # 对于应用和实例类型的题目，使用具体的实例作为选项
                examples = option_templates[category].get(question_type, [])
                random.shuffle(examples)
                # 确保正确选项是相关的应用实例
                if examples:
                    # 选择一个相关的实例作为正确选项
                    correct_option = random.choice(examples)
                    # 生成错误选项
                    while len(unique_errors) < 3 and examples:
                        example = examples.pop()
                        if example != correct_option and example not in unique_errors:
                            unique_errors.append(example)
            
            # 如果没有足够的错误选项，使用通用错误选项
            if len(unique_errors) < 3:
                while len(unique_errors) < 3 and temp_errors:
                    error = temp_errors.pop()
                    if error != correct_option and error not in unique_errors:
                        unique_errors.append(error)
                
                # 如果错误选项仍然不够，使用默认错误选项
                if len(unique_errors) < 3:
                    default_errors = error_templates['默认']['通用'].copy()
                    random.shuffle(default_errors)
                    for error in default_errors:
                        if error != correct_option and error not in unique_errors and len(unique_errors) < 3:
                            unique_errors.append(error)
            
            # 构建选项列表
            options = [correct_option] + unique_errors[:3]
            
            # 随机打乱选项顺序
            random.shuffle(options)
            correct_index = options.index(correct_option)
            
            # 创建题目对象
            question = {
                'question': question_text,
                'options': options,
                'answer': correct_index,
                'explanation': kp['content']
            }
            
            questions.append(question)
    
    # 随机打乱题目顺序
    random.shuffle(questions)
    
    return questions

# 用户登录API
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return jsonify({
                'status': 'success',
                'message': '登录成功',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['name'],
                    'totalScore': user['totalScore']
                }
            })
        else:
            return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 用户注册API
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        name = data.get('name')
        
        if not username or not password or not name:
            return jsonify({'status': 'error', 'message': '请填写完整信息'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
        
        # 检查姓名是否已存在
        cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': '姓名已存在'}), 400
        
        # 创建新用户
        cursor.execute('INSERT INTO users (username, password, name, totalScore) VALUES (?, ?, ?, ?)',
                   (username, password, name, 0))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '注册成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取所有章节
@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM chapters ORDER BY level, id')
        chapters = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(chapters)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户可用的章节
@app.route('/api/user-available-chapters', methods=['GET'])
def get_user_available_chapters():
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({'status': 'error', 'message': '缺少用户ID'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否是管理员（这里简单判断：用户名为admin）
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user and user['username'] == 'admin':
            # 管理员可以访问所有章节
            cursor.execute('SELECT * FROM chapters ORDER BY level, id')
            all_chapters = cursor.fetchall()
            conn.close()
            return jsonify([dict(chapter) for chapter in all_chapters])
        
        # 普通用户只能访问有权限的章节
        cursor.execute('''
            SELECT DISTINCT c.* 
            FROM chapters c
            LEFT JOIN user_course_permissions ucp ON c.id = ucp.chapter_id
            WHERE ucp.user_id = ? OR c.id IN (
                SELECT parent_id FROM user_course_permissions WHERE user_id = ?
            ) OR c.id IN (
                SELECT parent_id FROM chapters WHERE id IN (
                    SELECT chapter_id FROM user_course_permissions WHERE user_id = ?
                )
            )
            ORDER BY c.level, c.id
        ''', (user_id, user_id, user_id))
        
        available_chapters = cursor.fetchall()
        
        # 收集一级章节ID
        level1_chapter_ids = set()
        for chapter in available_chapters:
            chapter_dict = dict(chapter)
            if chapter_dict['level'] == 1:
                level1_chapter_ids.add(chapter_dict['id'])
            elif chapter_dict['level'] == 2 and chapter_dict['parent_id']:
                level1_chapter_ids.add(chapter_dict['parent_id'])
        
        # 获取所有可用的一级和二级章节
        all_chapters = []
        for chapter in available_chapters:
            chapter_dict = dict(chapter)
            if chapter_dict['level'] == 1 or (chapter_dict['level'] == 2 and chapter_dict['parent_id'] in level1_chapter_ids):
                all_chapters.append(chapter_dict)
        
        conn.close()
        return jsonify(all_chapters)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取知识点
@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    try:
        chapter_id = request.args.get('chapter_id', type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if chapter_id:
            cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (chapter_id,))
        else:
            cursor.execute('SELECT * FROM knowledge')
        
        knowledge = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(knowledge)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 生成题目API
@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    try:
        data = request.json
        first_level_id = data.get('first_level_id')
        second_level_id = data.get('second_level_id')
        chapter_id = data.get('chapter_id')
        count = data.get('count', 10)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 根据参数获取知识点
        if chapter_id:
            # 如果指定了章节ID，直接获取该章节的知识点
            cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (chapter_id,))
        elif second_level_id:
            # 如果指定了二级章节ID，获取该章节的知识点
            cursor.execute('SELECT * FROM knowledge WHERE chapter_id = ?', (second_level_id,))
        elif first_level_id:
            # 如果指定了一级章节ID，获取该章节下所有二级章节的知识点
            cursor.execute('''
                SELECT k.* FROM knowledge k
                JOIN chapters c ON k.chapter_id = c.id
                WHERE c.parent_id = ?
            ''', (first_level_id,))
        else:
            # 如果没有指定任何章节，获取所有知识点
            cursor.execute('SELECT * FROM knowledge')
        
        knowledge_points = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not knowledge_points:
            # 如果没有知识点，返回默认题目
            return jsonify([
                {
                    "question": "冷湖知识复习系统的主要功能是什么？",
                    "options": ["答题练习", "知识管理", "排行榜", "以上都是"],
                    "answer": "以上都是",
                    "explanation": "冷湖知识复习系统集成了答题练习、知识管理和排行榜等多种功能。"
                },
                {
                    "question": "以下哪项不是冷湖知识复习系统的特点？",
                    "options": ["AI生成题目", "实时排行榜", "多人PK对战", "离线使用"],
                    "answer": "离线使用",
                    "explanation": "冷湖知识复习系统需要联网使用，支持AI生成题目和实时排行榜等在线功能。"
                }
            ])
        
        # 使用已有的函数生成题目
        questions = generate_questions_from_knowledge_points(knowledge_points)
        
        # 限制题目数量
        if len(questions) > count:
            questions = questions[:count]
        
        return jsonify(questions)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 提交排名API
@app.route('/api/submit', methods=['POST'])
def submit_ranking():
    try:
        data = request.json
        name = data.get('name')
        score = data.get('score')
        correctCount = data.get('correctCount')
        time = data.get('time')
        date = data.get('date', datetime.now().isoformat())
        
        if not all([name, score is not None, correctCount is not None, time is not None]):
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 插入排名数据
        cursor.execute('''
            INSERT INTO rankings (name, score, correctCount, time, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, score, correctCount, time, date))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '提交成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 提交答题结果
@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        user_id = data.get('user_id')
        chapter_id = data.get('chapter_id')
        score = data.get('score')
        correct_count = data.get('correct_count')
        total_questions = data.get('total_questions')
        
        if not all([user_id, chapter_id, score is not None, correct_count is not None, total_questions]):
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户信息
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 更新用户总分
        new_total_score = user['totalScore'] + score
        cursor.execute('UPDATE users SET totalScore = ? WHERE id = ?', (new_total_score, user_id))
        
        # 记录到排行榜
        cursor.execute('''
            INSERT INTO rankings (name, score, correctCount, time, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['name'], score, correct_count, total_questions, datetime.now().isoformat()))
        
        # 更新答题时间记录
        cursor.execute('''
            SELECT interval_days FROM user_quiz_times
            WHERE user_id = ? AND chapter_id = ?
        ''', (user_id, chapter_id))
        quiz_time = cursor.fetchone()
        
        if quiz_time:
            interval_days = quiz_time[0]
            if interval_days < 7:
                interval_days += 1
            else:
                interval_days = 1
        else:
            interval_days = 1
        
        next_available_time = datetime.now() + timedelta(days=interval_days)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_quiz_times (user_id, chapter_id, last_quiz_time, next_available_time, interval_days)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, chapter_id, datetime.now().isoformat(), next_available_time.isoformat(), interval_days))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '答题结果已提交',
            'new_total_score': new_total_score,
            'next_available_time': next_available_time.isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取排行榜
@app.route('/api/rankings', methods=['GET'])
def get_rankings():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                name,
                SUM(score) as total_score,
                SUM(correctCount) as total_correct,
                SUM(time) as total_time,
                MIN(date) as first_date,
                COUNT(*) as quiz_count
            FROM rankings
            WHERE name != '匿名用户'
            GROUP BY name
            ORDER BY total_score DESC, total_time ASC
            LIMIT 50
        ''')
        
        rankings = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(rankings)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户信息
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, name, totalScore FROM users')
        users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 更新用户分数
@app.route('/api/users/<int:user_id>/score', methods=['PUT'])
def update_user_score(user_id):
    try:
        data = request.json
        score_change = data.get('score_change', 0)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户当前分数
        cursor.execute('SELECT totalScore FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        current_score = user[0]
        new_score = max(0, current_score + score_change)
        
        # 更新分数
        cursor.execute('UPDATE users SET totalScore = ? WHERE id = ?', (new_score, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '分数更新成功',
            'new_score': new_score
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 添加知识点
@app.route('/api/knowledge', methods=['POST'])
def add_knowledge():
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        chapter_id = data.get('chapter_id')
        
        if not all([title, content, category]):
            return jsonify({'status': 'error', 'message': '请填写完整信息'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge (title, content, category, chapter_id)
            VALUES (?, ?, ?, ?)
        ''', (title, content, category, chapter_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '知识点添加成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 删除知识点
@app.route('/api/knowledge/<int:knowledge_id>', methods=['DELETE'])
def delete_knowledge(knowledge_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM knowledge WHERE id = ?', (knowledge_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '知识点删除成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 添加章节
@app.route('/api/chapters', methods=['POST'])
def add_chapter():
    try:
        data = request.json
        name = data.get('name')
        code = data.get('code')
        level = data.get('level', 1)
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({'status': 'error', 'message': '请填写章节名称'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chapters (name, code, level, parent_id)
            VALUES (?, ?, ?, ?)
        ''', (name, code, level, parent_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '章节添加成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取单个章节
@app.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM chapters WHERE id = ?', (chapter_id,))
        chapter = cursor.fetchone()
        
        if not chapter:
            conn.close()
            return jsonify({'status': 'error', 'message': '章节不存在'}), 404
        
        conn.close()
        return jsonify(dict(chapter))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 更新章节
@app.route('/api/chapters/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    try:
        data = request.json
        name = data.get('name')
        code = data.get('code')
        level = data.get('level')
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({'status': 'error', 'message': '请填写章节名称'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查章节是否存在
        cursor.execute('SELECT * FROM chapters WHERE id = ?', (chapter_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': '章节不存在'}), 404
        
        # 更新章节
        cursor.execute('''
            UPDATE chapters 
            SET name = ?, code = ?, level = ?, parent_id = ? 
            WHERE id = ?
        ''', (name, code, level, parent_id, chapter_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '章节更新成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 删除章节
@app.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM chapters WHERE id = ?', (chapter_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '章节删除成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 设置用户课程权限
@app.route('/api/user-course-permissions', methods=['POST'])
def set_user_course_permissions():
    try:
        data = request.json
        user_id = data.get('user_id')
        chapter_ids = data.get('chapter_ids', [])
        
        if not user_id:
            return jsonify({'status': 'error', 'message': '缺少用户ID'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 删除用户现有的权限
        cursor.execute('DELETE FROM user_course_permissions WHERE user_id = ?', (user_id,))
        
        # 添加新的权限
        for chapter_id in chapter_ids:
            cursor.execute('''
                INSERT INTO user_course_permissions (user_id, chapter_id)
                VALUES (?, ?)
            ''', (user_id, chapter_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '权限设置成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户课程权限
@app.route('/api/user-course-permissions/<int:user_id>', methods=['GET'])
def get_user_course_permissions(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chapter_id FROM user_course_permissions
            WHERE user_id = ?
        ''', (user_id,))
        
        permissions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(permissions)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取用户信息
@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        conn.close()
        return jsonify(dict(user))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取在线用户
@app.route('/api/online-users', methods=['GET'])
def get_online_users():
    try:
        # 返回在线用户列表
        users_list = []
        for user_id, user_info in online_users.items():
            users_list.append({
                'id': user_id,
                'name': user_info['name'],
                'totalScore': user_info['totalScore']
            })
        
        return jsonify(users_list)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取科学百科知识
@app.route('/api/science-encyclopedia', methods=['GET'])
def get_science_encyclopedia():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM science_encyclopedia ORDER BY RANDOM() LIMIT 20')
        items = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(items)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 添加科学百科知识
@app.route('/api/science-encyclopedia', methods=['POST'])
def add_science_encyclopedia():
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        difficulty = data.get('difficulty', 'easy')
        
        if not all([title, content, category]):
            return jsonify({'status': 'error', 'message': '请填写完整信息'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO science_encyclopedia (title, content, category, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, content, category, difficulty, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '科学百科知识添加成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 创建PK挑战
@app.route('/api/pk-challenges', methods=['POST'])
def create_pk_challenge():
    try:
        data = request.json
        challenger_id = data.get('challenger_id')
        opponent_id = data.get('opponent_id')
        
        if not all([challenger_id, opponent_id]):
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户是否在线
        if opponent_id not in online_users:
            conn.close()
            return jsonify({'status': 'error', 'message': '对方不在线'}), 400
        
        # 创建PK挑战
        cursor.execute('''
            INSERT INTO pk_challenges (challenger_id, opponent_id, status, created_at)
            VALUES (?, ?, 'pending', ?)
        ''', (challenger_id, opponent_id, datetime.now().isoformat()))
        
        challenge_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 通过WebSocket通知对手
        socketio.emit('pk_challenge_request', {
            'challenge_id': challenge_id,
            'challenger_id': challenger_id,
            'challenger_name': online_users[challenger_id]['name']
        }, room=f'user_{opponent_id}')
        
        return jsonify({'status': 'success', 'message': 'PK挑战创建成功', 'challenge_id': challenge_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 接受PK挑战
@app.route('/api/pk-challenges/<int:challenge_id>/accept', methods=['POST'])
def accept_pk_challenge(challenge_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新挑战状态
        cursor.execute('''
            UPDATE pk_challenges
            SET status = 'active'
            WHERE id = ?
        ''', (challenge_id,))
        
        # 获取挑战信息
        cursor.execute('SELECT * FROM pk_challenges WHERE id = ?', (challenge_id,))
        challenge = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if not challenge:
            return jsonify({'status': 'error', 'message': '挑战不存在'}), 404
        
        # 通知双方开始挑战
        socketio.emit('pk_challenge_started', {
            'challenge_id': challenge_id,
            'challenger_id': challenge['challenger_id'],
            'opponent_id': challenge['opponent_id']
        }, room=f'challenge_{challenge_id}')
        
        return jsonify({'status': 'success', 'message': '已接受挑战'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 提交PK答案
@app.route('/api/pk-challenges/<int:challenge_id>/answer', methods=['POST'])
def submit_pk_answer(challenge_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        is_correct = data.get('is_correct')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取挑战信息
        cursor.execute('SELECT * FROM pk_challenges WHERE id = ?', (challenge_id,))
        challenge = cursor.fetchone()
        
        if not challenge:
            conn.close()
            return jsonify({'status': 'error', 'message': '挑战不存在'}), 404
        
        # 更新分数
        if user_id == challenge['challenger_id']:
            if is_correct:
                cursor.execute('''
                    UPDATE pk_challenges
                    SET challenger_score = challenger_score + 1
                    WHERE id = ?
                ''', (challenge_id,))
        elif user_id == challenge['opponent_id']:
            if is_correct:
                cursor.execute('''
                    UPDATE pk_challenges
                    SET opponent_score = opponent_score + 1
                    WHERE id = ?
                ''', (challenge_id,))
        
        # 更新当前题目
        cursor.execute('''
            UPDATE pk_challenges
            SET current_question = current_question + 1
            WHERE id = ?
        ''', (challenge_id,))
        
        # 获取更新后的挑战信息
        cursor.execute('SELECT * FROM pk_challenges WHERE id = ?', (challenge_id,))
        updated_challenge = cursor.fetchone()
        
        # 检查是否完成
        completed = updated_challenge['current_question'] >= updated_challenge['total_questions']
        
        if completed:
            # 计算胜负
            challenger_score = updated_challenge['challenger_score']
            opponent_score = updated_challenge['opponent_score']
            
            winner_id = None
            loser_id = None
            
            if challenger_score > opponent_score:
                winner_id = challenge['challenger_id']
                loser_id = challenge['opponent_id']
            elif opponent_score > challenger_score:
                winner_id = challenge['opponent_id']
                loser_id = challenge['challenger_id']
            
            # 更新用户积分
            if winner_id:
                cursor.execute('''
                    UPDATE users SET totalScore = totalScore + 3 WHERE id = ?
                ''', (winner_id,))
            
            if loser_id:
                cursor.execute('''
                    UPDATE users SET totalScore = CASE WHEN totalScore > 1 THEN totalScore - 1 ELSE 0 END WHERE id = ?
                ''', (loser_id,))
            
            # 更新挑战状态
            cursor.execute('''
                UPDATE pk_challenges
                SET status = 'completed', completed_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), challenge_id))
            
            # 通知双方结果
            socketio.emit('pk_challenge_completed', {
                'challenge_id': challenge_id,
                'challenger_id': challenge['challenger_id'],
                'opponent_id': challenge['opponent_id'],
                'challenger_score': challenger_score,
                'opponent_score': opponent_score,
                'winner_id': winner_id,
                'loser_id': loser_id
            }, room=f'challenge_{challenge_id}')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '答案已提交',
            'completed': completed,
            'current_question': updated_challenge['current_question'],
            'challenger_score': updated_challenge['challenger_score'],
            'opponent_score': updated_challenge['opponent_score']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 创建BOSS挑战
@app.route('/api/boss-challenges', methods=['POST'])
def create_boss_challenge():
    try:
        data = request.json
        creator_id = data.get('creator_id')
        boss_name = data.get('boss_name', '世界BOSS')
        boss_hp = data.get('boss_hp', 100)
        
        if not creator_id:
            return jsonify({'status': 'error', 'message': '创建者ID不能为空'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO boss_challenges (creator_id, boss_name, boss_hp, boss_max_hp, status, created_at)
            VALUES (?, ?, ?, ?, 'active', ?)
        ''', (creator_id, boss_name, boss_hp, boss_hp, datetime.now().isoformat()))
        
        boss_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 通知所有客户端有新的BOSS挑战
        socketio.emit('new_boss_challenge', {'boss_id': boss_id, 'boss_name': boss_name})
        
        return jsonify({'status': 'success', 'message': 'BOSS挑战创建成功', 'boss_id': boss_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 获取BOSS挑战列表
@app.route('/api/boss-challenges', methods=['GET'])
def get_boss_challenges():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT bc.*, u.name as creator_name
            FROM boss_challenges bc
            LEFT JOIN users u ON bc.creator_id = u.id
            WHERE bc.status = 'active'
            ORDER BY bc.created_at DESC
        ''')
        
        bosses = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(bosses)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 删除BOSS挑战
@app.route('/api/boss-challenges/<int:boss_id>', methods=['DELETE'])
def delete_boss_challenge(boss_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查BOSS是否存在
        cursor.execute('SELECT * FROM boss_challenges WHERE id = ?', (boss_id,))
        boss = cursor.fetchone()
        
        if not boss:
            conn.close()
            return jsonify({'status': 'error', 'message': 'BOSS挑战不存在'}), 404
        
        # 删除BOSS参与者记录
        cursor.execute('DELETE FROM boss_participants WHERE boss_id = ?', (boss_id,))
        
        # 删除BOSS挑战记录
        cursor.execute('DELETE FROM boss_challenges WHERE id = ?', (boss_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'BOSS挑战删除成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 参与BOSS挑战
@app.route('/api/boss-challenges/<int:boss_id>/participate', methods=['POST'])
def participate_boss_challenge(boss_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': '用户ID不能为空'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查BOSS是否存在
        cursor.execute('SELECT * FROM boss_challenges WHERE id = ?', (boss_id,))
        boss = cursor.fetchone()
        
        if not boss:
            conn.close()
            return jsonify({'status': 'error', 'message': 'BOSS挑战不存在'}), 404
        
        # 检查是否已参与
        cursor.execute('''
            SELECT * FROM boss_participants
            WHERE boss_id = ? AND user_id = ?
        ''', (boss_id, user_id))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': '已参与此BOSS挑战'}), 400
        
        # 添加参与记录
        cursor.execute('''
            INSERT INTO boss_participants (boss_id, user_id)
            VALUES (?, ?)
        ''', (boss_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': '已参与BOSS挑战'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 提交BOSS答案
@app.route('/api/boss-challenges/<int:boss_id>/answer', methods=['POST'])
def submit_boss_answer(boss_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        is_correct = data.get('is_correct')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取BOSS信息
        cursor.execute('SELECT * FROM boss_challenges WHERE id = ?', (boss_id,))
        boss = cursor.fetchone()
        
        if not boss:
            conn.close()
            return jsonify({'status': 'error', 'message': 'BOSS挑战不存在'}), 404
        
        if boss['status'] != 'active':
            conn.close()
            return jsonify({'status': 'error', 'message': 'BOSS挑战已结束'}), 400
        
        if is_correct:
            # 扣除BOSS血量
            new_hp = max(0, boss['boss_hp'] - 1)
            cursor.execute('''
                UPDATE boss_challenges SET boss_hp = ? WHERE id = ?
            ''', (new_hp, boss_id))
            
            # 更新用户正确答题数
            cursor.execute('''
                UPDATE boss_participants
                SET correct_count = correct_count + 1
                WHERE boss_id = ? AND user_id = ?
            ''', (boss_id, user_id))
            
            # 通知所有客户端BOSS血量更新
            socketio.emit('boss_hp_update', {
                'boss_id': boss_id,
                'current_hp': new_hp,
                'max_hp': boss['boss_max_hp']
            })
            
            # 检查BOSS是否被击败
            if new_hp <= 0:
                # 更新BOSS状态
                cursor.execute('''
                    UPDATE boss_challenges
                    SET status = 'completed', completed_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), boss_id))
                
                # 给所有参与者发放奖励
                cursor.execute('''
                    UPDATE users u
                    SET totalScore = totalScore + 3
                    WHERE id IN (SELECT user_id FROM boss_participants WHERE boss_id = ?)
                ''', (boss_id))
                
                cursor.execute('''
                    UPDATE boss_participants
                    SET received_reward = 1
                    WHERE boss_id = ?
                ''', (boss_id,))
                
                # 通知所有客户端BOSS被击败
                socketio.emit('boss_defeated', {
                    'boss_id': boss_id,
                    'boss_name': boss['boss_name']
                })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': '答案已提交',
            'boss_defeated': new_hp <= 0 if is_correct else False
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    print(f'客户端已连接: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'客户端已断开: {request.sid}')
    # 从在线用户列表中移除
    for user_id, user_info in list(online_users.items()):
        if user_info['sid'] == request.sid:
            del online_users[user_id]
            print(f'用户 {user_id} 离线')
            break

@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(f'user_{user_id}')
        
        # 获取用户信息并添加到在线列表
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, totalScore FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            online_users[user_id] = {
                'name': user['name'],
                'totalScore': user['totalScore'],
                'sid': request.sid
            }
            print(f'用户 {user_id} ({user["name"]}) 上线')

@socketio.on('join_challenge')
def handle_join_challenge(data):
    challenge_id = data.get('challenge_id')
    if challenge_id:
        join_room(f'challenge_{challenge_id}')
        print(f'加入挑战房间: {challenge_id}')

@socketio.on('leave_challenge')
def handle_leave_challenge(data):
    challenge_id = data.get('challenge_id')
    if challenge_id:
        leave_room(f'challenge_{challenge_id}')
        print(f'离开挑战房间: {challenge_id}')

# 运行服务器
if __name__ == '__main__':
    import sys
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='冷湖知识复习系统后端服务器')
    parser.add_argument('--port', type=int, default=9000, help='服务器端口')
    args = parser.parse_args()
    
    # 启动服务器
    print(f'服务器启动在端口 {args.port}...')
    socketio.run(app, host='0.0.0.0', port=args.port, debug=True, allow_unsafe_werkzeug=True)