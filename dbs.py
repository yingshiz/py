import sqlite3
import os
def load_db():
    # 创建数据库连接
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dbfile = os.path.join(current_dir, 'strategy.db')
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    # 创建strategy表
    # 创建一个表
    cursor.execute('')
    conn.commit()
    conn.close()
    print('加载strategy.db数据库...', end='')
    print('\033[92m', 'ok', '\033[0m')