import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'quiz.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def add_science_knowledge():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    science_data = [
        {
            'title': '水的三态变化',
            'content': '水有三种状态：固态（冰）、液态（水）、气态（水蒸气）。水的三态变化是物理变化，由温度变化引起。水在0°C以下会变成固态，0°C到100°C之间是液态，100°C以上会变成气态。',
            'category': '物理',
            'difficulty': 'easy'
        },
        {
            'title': '哺乳动物的特征',
            'content': '哺乳动物的主要特征包括：胎生、哺乳、体表被毛、体温恒定、心脏四腔。常见的哺乳动物有狗、猫、牛、羊、马、鲸鱼、蝙蝠等。',
            'category': '生物',
            'difficulty': 'easy'
        },
        {
            'title': '植物的光合作用',
            'content': '光合作用是植物利用阳光、水和二氧化碳制造养分的过程。植物通过叶绿素吸收阳光，在叶绿体中进行光合作用，产生氧气和葡萄糖。光合作用对地球生态系统至关重要。',
            'category': '生物',
            'difficulty': 'easy'
        },
        {
            'title': '太阳系的行星',
            'content': '太阳系有八大行星：水星、金星、地球、火星、木星、土星、天王星、海王星。地球是唯一已知存在生命的行星。木星是太阳系最大的行星。',
            'category': '天文',
            'difficulty': 'easy'
        },
        {
            'title': '地球的自转和公转',
            'content': '地球自转产生昼夜交替，自转一周约24小时。地球公转产生四季变化，公转一周约365天。地球自转轴倾斜23.5度，这是产生四季变化的原因。',
            'category': '天文',
            'difficulty': 'easy'
        },
        {
            'title': '声音的传播',
            'content': '声音需要介质才能传播，可以在固体、液体和气体中传播，但不能在真空中传播。声音在固体中传播最快，在气体中传播最慢。声音的速度约为340米/秒。',
            'category': '物理',
            'difficulty': 'easy'
        },
        {
            'title': '昆虫的特征',
            'content': '昆虫是节肢动物，身体分为头、胸、腹三部分，有三对足，通常有两对翅膀。常见的昆虫有蚂蚁、蜜蜂、蝴蝶、蜻蜓等。昆虫是世界上种类最多的动物群体。',
            'category': '生物',
            'difficulty': 'easy'
        },
        {
            'title': '水的循环',
            'content': '水在地球上不断循环：海洋和湖泊的水蒸发成水蒸气，水蒸气上升遇冷凝结成云，云中的水滴聚集形成雨雪降落到地面，雨水汇入河流和海洋，完成水循环。',
            'category': '地理',
            'difficulty': 'easy'
        },
        {
            'title': '磁铁的性质',
            'content': '磁铁有两极：北极和南极。同极相斥，异极相吸。磁铁可以吸引铁、镍、钴等金属。地球本身就是一个巨大的磁铁，有南北磁极。',
            'category': '物理',
            'difficulty': 'easy'
        },
        {
            'title': '月亮的相位',
            'content': '月亮有八个主要相位：新月、上弦月、满月、下弦月等。月亮的相位变化是由于月球绕地球公转时，太阳、地球、月球三者的相对位置变化造成的。',
            'category': '天文',
            'difficulty': 'easy'
        },
        {
            'title': '食物链',
            'content': '食物链描述了生态系统中能量流动的路径。食物链从生产者（植物）开始，经过初级消费者（食草动物）、次级消费者（食肉动物），最终到分解者。食物链形成了复杂的食物网。',
            'category': '生物',
            'difficulty': 'easy'
        },
        {
            'title': '彩虹的形成',
            'content': '彩虹是阳光通过雨滴时发生折射、反射和色散形成的。阳光由七种颜色组成：红、橙、黄、绿、蓝、靛、紫。雨滴就像小棱镜，将阳光分解成彩虹。',
            'category': '物理',
            'difficulty': 'easy'
        },
        {
            'title': '火山',
            'content': '火山是地球内部熔岩喷发到地表形成的。火山爆发时会喷出熔岩、火山灰和气体。火山可以形成新的岛屿和山脉。世界上著名的火山有富士山、维苏威火山等。',
            'category': '地理',
            'difficulty': 'easy'
        },
        {
            'title': '鸟类的特征',
            'content': '鸟类的主要特征包括：体表被羽毛、前肢变成翼、恒温、卵生。鸟类有中空的骨骼，适合飞行。常见的鸟类有麻雀、燕子、老鹰、鸽子等。',
            'category': '生物',
            'difficulty': 'easy'
        },
        {
            'title': '简单电路',
            'content': '简单电路由电源、导线和用电器组成。电流从电源正极出发，通过导线和用电器，回到电源负极。电路有通路、断路和短路三种状态。开关可以控制电路的通断。',
            'category': '物理',
            'difficulty': 'easy'
        },
        {
            'title': '云的形成',
            'content': '云是由水蒸气凝结成的小水滴或冰晶组成的。当空气上升时，温度降低，水蒸气凝结成小水滴，形成云。不同高度的云有不同的名称，如积云、层云、卷云等。',
            'category': '地理',
            'difficulty': 'easy'
        },
        {
            'title': '鱼类的特征',
            'content': '鱼类生活在水中，用鳃呼吸，用鳍游泳。鱼类的身体表面有鳞片，体温随环境变化。常见的鱼类有鲤鱼、金鱼、鲨鱼、金枪鱼等。',
            'category': '生物',
            'difficulty': 'easy'
        },
        {
            'title': '重力和浮力',
            'content': '重力是地球对物体的吸引力，方向竖直向下。浮力是液体或气体对浸在其中的物体的向上托力。当浮力大于重力时，物体会上浮；当浮力小于重力时，物体会下沉。',
            'category': '物理',
            'difficulty': 'easy'
        },
        {
            'title': '四季的形成',
            'content': '四季的形成是因为地球自转轴倾斜23.5度，绕太阳公转时，太阳直射点在南北回归线之间移动。当太阳直射北半球时，北半球是夏季；直射南半球时，南半球是夏季。',
            'category': '地理',
            'difficulty': 'easy'
        },
        {
            'title': '青蛙的生命周期',
            'content': '青蛙的生命周期包括卵、蝌蚪、幼蛙、成蛙四个阶段。青蛙是两栖动物，幼体生活在水中用鳃呼吸，成体可以生活在陆地或水中用肺和皮肤呼吸。',
            'category': '生物',
            'difficulty': 'easy'
        }
    ]
    
    for item in science_data:
        cursor.execute('''
            INSERT INTO science_encyclopedia (title, content, category, difficulty, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (item['title'], item['content'], item['category'], item['difficulty']))
    
    conn.commit()
    conn.close()
    print(f'成功添加 {len(science_data)} 条科学百科知识')

if __name__ == '__main__':
    add_science_knowledge()
