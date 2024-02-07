import sqlite3
def load_db():
    # 创建数据库连接
    conn = sqlite3.connect('trade.db')
    cursor = conn.cursor()
    # 创建trade表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        price REAL,
        num INTEGER,
        time INTEGER,
        status INTEGER
    )
    ''')
    conn.commit()
    conn.close()
    print('加载数据库...', end='')
    print('\033[92m', 'ok', '\033[0m')