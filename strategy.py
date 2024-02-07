import requests
import json
import os
import datetime
import requests
import json
import pandas as pd
import numpy as np
import sys
import sqlite3
import dbs
import time
import threading
from dealData import update_data
from flask import Flask, jsonify
dbs.load_db()
app = Flask(__name__)
symbols = []
i = 0
global_data = pd.DataFrame()
# 定义获取symbols列表的函数
def get_symbol_list():
    url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple?page=1&num=600&sort=symbol&asc=1&node=hskzz_z&_s_r_a=setlen"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    result = [d['symbol'] for d in data if float(d['open']) > 0]
    symbols= ','.join(result)
    symbols=symbols.upper()
    return symbols
# 定义检查并获取缓存数据的函数
def get_cached_symbols():
    cache_file = 'symbols.txt'
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在的目录
    cache_file = os.path.join(current_dir, cache_file)  # 构建完整的文件路径
    # 获取当前日期
    current_date = datetime.date.today()
    # 检查是否存在缓存文件
    if os.path.exists(cache_file) and (datetime.date.fromtimestamp(os.path.getmtime(cache_file)) == current_date):
        # 从缓存文件中读取数据
        with open(cache_file, 'r') as f:
            symbols = f.read()
    else:
        symbols = get_symbol_list()
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(symbols)
    return symbols
#爬取数据
def get_stock_data(symbols):
    #symbols = 'SH113595,SZ127014';#debug
    #url = f"https://stock.xueqiu.com/v5/stock/batch/quote.json?symbol={symbols}"
    global i
    url = f'http://192.168.123.107/a.php?i={i}'
    i+=1
    if i>2:
        i=0
    cookie = "xq_a_token=edbee4e5d1e92f98548629214a6e17fe06486a8f"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headers = {
        "Cookie": cookie,
        "User-Agent": user_agent
    }
    response = requests.get(url, headers=headers)
    if(response.status_code==404):
        print(f'{url}访问失败！！！！')
        return ''
    if(response.status_code==403):
        print('要更改cookie xq_a_token')
        return ''
    data = response.json()
    '''cache_file = 'data.txt'
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在的目录
    cache_file = os.path.join(current_dir, cache_file)  # 构建完整的文件路径
    with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))
    '''
    return data
#对爬取到的数据进行pandas处理
def fetch_data():
    global symbols,global_data
    results = get_stock_data(symbols)
    datalist = [item['quote'] for item in results['data']['items']]
    global_data = update_data(global_data,datalist)
    '''# 获取当前时间
    now = datetime.datetime.now()
    # 将时间格式化为“时分秒”的格式
    time_str = now.strftime("%H%M%S")
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在的目录
    daily_data_dir = os.path.join(current_dir, 'daily_data')  # daily_data目录
    file_path = os.path.join(daily_data_dir, f'{time_str}.csv')  # 构建完整的文件路径
    global_data.to_csv(file_path, index=False)'''
    strategy()
#进行策略，设置买卖点，记录买卖信息到数据库
def strategy():
    global global_data
    t = datetime.datetime.now()
    current_time = int(datetime.datetime.now().timestamp())
    # 计算10秒前的时间
    seconds_ago = t - datetime.timedelta(seconds=10)
    # 计算1分钟前的时间
    minute_ago = t - datetime.timedelta(minutes=1)
    # 转换为毫秒级时间戳
    seconds_ago = int(seconds_ago.timestamp() * 1000)
    minute_ago = int(minute_ago.timestamp() * 1000)
    d = global_data.copy()
    '''买入策略'''
    #condition = (d['up'] > 0) & (d['buy_time'] == 0) & (d['amount_rank'] < 2 & (d['up']<seconds_ago) & (d['up']>minute_ago))
    condition = (d['up'] > 0) & (d['buy_time'] == 0) & (d['amount_rank'] < 2)
    global_data.loc[condition, 'buy_time'] = current_time
    global_data.loc[condition, 'sale_time'] = 0
    '''卖出策略'''
    condition = (d['down'] > 0) & (d['buy_time'] > 0)
    global_data.loc[condition, 'sale_time'] = current_time
    global_data.loc[condition, 'buy_time'] = 0
    #print(d)
    #print(global_data)
    diff = d.compare(global_data, align_axis=1)
    if not diff.empty:
        changed_data = global_data.iloc[diff.index]
        print(changed_data)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dbfile = os.path.join(current_dir, 'strategy.db')
        conn = sqlite3.connect(dbfile)
        dt = datetime.datetime.now().strftime('%Y%m%d')
        table_name = f't{dt}'  # 使用当天日期作为表名
        changed_data.loc[:, 'insert_time'] = current_time
        changed_data.to_sql(table_name, conn, if_exists='append', index=False)
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        status_exists = any(column[1] == "status" for column in columns)
        # 如果status字段不存在，则添加该字段并设置默认值为0
        if not status_exists:
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN status INTEGER DEFAULT 0")
        conn.commit()
        conn.close()
    print('.', end='.')
def fetch_data_thread(stop_event):
    while not stop_event.is_set():
        fetch_data()
        time.sleep(3)  # 暂停3秒
@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(global_data.to_dict('records'))
if __name__ == "__main__":
        #初始化数据库
        conn = sqlite3.connect('db.sqlite')
        symbols = get_cached_symbols()
        stop_event = threading.Event()
        thread = threading.Thread(target=fetch_data_thread, args=(stop_event,))
        thread.start()
        app.run(host='0.0.0.0', port=5001)
