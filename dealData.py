import pandas as pd
def update_data(global_data,datalist):
    fields = ['symbol','name','percent', 'current', 'avg_price', 'amount','open','last_close','high','low','time']
    if len(global_data) == 0:
        df = pd.DataFrame(datalist)
        data = df[fields]
        data = data.assign(up=0,down=0,amount_rank=0,buy_time=0,sale_time=0)#新增字段
    else:
        df = pd.DataFrame(datalist)
        update_data = df[fields]
        data = pd.merge(global_data, update_data, on='symbol', how='left',suffixes=('','_y'))
        #策略准备条件
        condition = (data['current'] > data['avg_price']) & (data['current_y'] < data['avg_price_y']) & (data['time'] < data['time_y'])#跌破均价
        data.loc[condition, 'down'] = data['time_y']
        data.loc[condition, 'up'] = 0
        condition = (data['current'] < data['avg_price']) & (data['current_y'] > data['avg_price_y']) & (data['time'] < data['time_y'])#上穿均价
        data.loc[condition, 'up'] = data['time_y']
        data.loc[condition, 'down'] = 0
        #更新字段值
        condition = (data['time'] < data['time_y'])
        data.loc[condition, 'amount_rank'] = data['amount_y'].rank(ascending=False, method='min')
        #print(data)
        for column_name in fields:
            if(column_name!='symbol'):
                data.loc[condition, column_name] = data[f'{column_name}_y']
    fields += ['up','down','amount_rank','buy_time','sale_time'] #新增字段
    global_data = data[fields]
    return global_data