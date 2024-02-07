#http://192.168.123.30:5000/
import sqlite3
from flask import Flask, request, jsonify,send_file
import os
import time
import subprocess
import pyautogui
import pygetwindow as gw
import sys
from datetime import datetime
from multiprocessing import Process
import db
from collections import namedtuple
import threading
db.load_db()
# 定义海通证券应用程序的路径和参数
htsc_path = 'D:\\htzq\\海通证券金融终端独立下单2.0\\xiadan.exe'  # 应用程序路径
htsc_args = ''  # 应用程序参数（如果有的话）
app = Flask(__name__)
#每步操作前，需执行下面检测修复代码
def check_fix():
    active_window = pyautogui.getActiveWindow()
    if(active_window!='网上股票交易系统5.0'):
        pyautogui.press('enter')
@app.route('/')
def index():
    return send_file('index.html', as_attachment=False)
@app.route('/reload', methods=['GET'])
def reload():
    # 创建子进程
    shutdown_server()
    os.system("cmd /c start_server.bat")
    return 'reload'
@app.route('/exit_htsc', methods=['GET'])
def exit_htsc():
    # 查找名称为“网上股票交易系统5.0”的窗口
    trading_window = gw.getWindowsWithTitle('网上股票交易系统5.0')
    # 关闭窗口
    if len(trading_window) > 0:
        trading_window[0].close()
    return '退出海通'
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
#海通交易软件
@app.route('/start_htsc', methods=['GET'])
def start_htsc():
    if not bring_trading_window_to_front():
        subprocess.Popen([htsc_path, htsc_args])  # 启动海通证券应用程序
        auto_login()
    return 'start_htsc'
@app.route('/auto_buynew', methods=['GET'])
def auto_buynew():
    if not bring_trading_window_to_front():
        return 'Not in trading software window'
    #新股申购
    check_fix()
    pyautogui.moveTo(70, 180)
    pyautogui.click()
    time.sleep(0.5)
    #可转债申购
    check_fix()
    pyautogui.moveTo(70, 280)
    pyautogui.click()
    time.sleep(0.5)
    #刷新
    check_fix()
    pyautogui.moveTo(680, 300)
    pyautogui.click()
    time.sleep(1)
    #第1个
    check_fix()
    pyautogui.moveTo(680, 350)
    pyautogui.doubleClick()
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    #第2个
    check_fix()
    pyautogui.moveTo(680, 375)
    pyautogui.doubleClick()
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    #第3个
    check_fix()
    pyautogui.moveTo(680, 400)
    pyautogui.doubleClick()
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    #第4个
    check_fix()
    pyautogui.moveTo(680, 425)
    pyautogui.doubleClick()
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)
    pyautogui.press('enter')
    return 'auto_buynew'
def auto_login():
    time.sleep(2)  # 等待登录界面出现（可以根据实际情况调整等待时间）
    # 获取最上
    # 面的窗口信息159357
    active_window = pyautogui.getActiveWindow()
    if active_window.title=='':
        pyautogui.typewrite('159357', interval=0)
        pyautogui.press('enter')  # 按下回车键
    handle_popup()
def handle_popup():
    time.sleep(2)
    # 关闭提示框
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(x=screen_width // 2, y=screen_height // 2 + 130)
    pyautogui.click()
    # 最大化交易软件窗口
    time.sleep(1)
    pyautogui.hotkey("win", "up")  # 按下Windows键和向上键以最大化窗口
    # 启动buy_stock函数
    #买卖预热
    time.sleep(1)
    trade_do('128128','buy','120','0')
@app.route('/trade_api', methods=['GET'])
def trade_api():
    code = request.args.get('code')
    action = request.args.get('action')
    price = request.args.get('price')
    num = request.args.get('num')
    trade_do(code,action,price,num)
'''
交易队列任务
'''
def trade_cron_thread(stop_event):
    while not stop_event.is_set():
        trade_cron()
        #print('trade_cron_thread is running...')
        time.sleep(1)
#@app.route('/trade_cron', methods=['GET'])
def trade_cron():
    conn = sqlite3.connect('strategy.db')
    cursor = conn.cursor()
    # 每隔一秒从trade表取一条记录进行交易操作
    fstr = 'symbol,name,percent,current,avg_price,amount,open, last_close, high,low,time,up,down,amount_rank,buy_time,sale_time,insert_time, status'
    dt = datetime.now().strftime('%Y%m%d')
    table_name = f't{dt}'
    try:
        cursor.execute(f"SELECT {fstr} FROM {table_name} WHERE status = 0 ORDER BY insert_time ASC LIMIT 1")
        record = cursor.fetchone()
        if record:
            # 定义一个命名元组
            TradeRecord = namedtuple('TradeRecord', fstr.replace(',',' '))
            record = TradeRecord(*record)
            symbol = record.symbol
            time = record.time
            code = symbol.replace('SH','').replace('SZ','')
            if record.buy_time>0:
                action = 'buy'
            if record.sale_time>0:
                action = 'sale'
            trade_do(code,action,str(record.current),'10')
            # 处理完毕后设置status为1
            sql = f"UPDATE {table_name} SET status = 1 WHERE symbol = '{symbol}' and time= '{time}'"
            cursor.execute(sql)
            conn.commit()
            conn.close()
            return '交易完成'
        else:
            conn.close()
            return '没有可交易记录'
    except Exception as e:
        return str(e)
    ''' while True:
        '''
#执行交易任务
def trade_do(code, action, price, num):
    if not bring_trading_window_to_front():
        return 'Not in trading software window'
    check_fix()
    time.sleep(0.2)
    if action == 'buy':
        pyautogui.press('f2')
        pyautogui.press('f1')
    elif action == 'sale':
        pyautogui.press('f1')
        pyautogui.press('f2')
    else:
        return 'Invalid action'
    pyautogui.typewrite(code, interval=0)
    time.sleep(0.2)
    pyautogui.press('enter')
    pyautogui.typewrite(price, interval=0)
    pyautogui.press('enter')
    pyautogui.typewrite(num, interval=0)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')
    return f'{action} stock with code={code}, price={price}, num={num}'
#买卖信号,写进数据库
@app.route('/trade', methods=['GET'])
def trade():
    code = request.args.get('code')
    action = request.args.get('action')
    price = float(request.args.get('price'))
    num = int(request.args.get('num'))
    time_now = int(time.time())
    # 获取当前时间
    now = datetime.now()
    # 将当前时间转换为特定格式的字符串
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('trade.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trade (code, price, num, time,timestamp, status,action) VALUES (?, ?, ?, ?,?, ?,?)", (code, price, num,formatted_time, time_now, 0,action))
    conn.commit()
    conn.close()
    return f"{action}股票代码：{code}，价格：{price}，数量：{num}"
def bring_trading_window_to_front():
    trading_window = gw.getWindowsWithTitle('网上股票交易系统5.0')
    if len(trading_window) > 0:
        trading_window[0].activate()  # 激活窗口
        trading_window[0].maximize()  # 最大化窗口
        return True
    else:
        return False
if __name__ == '__main__':
    stop_event = threading.Event()
    thread = threading.Thread(target=trade_cron_thread, args=(stop_event,))
    thread.start()
    app.run(host='0.0.0.0', port=5000)