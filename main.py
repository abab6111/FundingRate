import pygsheets
import pathlib
import os
import ccxt
import config
import pandas as pd


ftx = ccxt.ftx({
    'apiKey': config.API_KEY,
    'secret': config.API_SECRET,
    'enableRateLimit': True,
    'headers': {'FTX-SUBACCOUNT': 'FundingRate'} # uncomment line if using subaccount
})

def percentage(funding_rate_str): #百分比轉小數
    take_out_percert = float(funding_rate_str.strip('%'))
    add_double_zero = take_out_percert/100
    return add_double_zero

def scie_to_decimal(num): # 科學符號轉小數點
    x = '{:.10f}'.format(num)
    return x

def turn_to_percentage(num): #轉成百分比
    x = '{:.4%}'.format(num)
    return x

def spot_entry_price(balance_data,spot_symbol):
    balance_dataframe = pd.DataFrame(balance_data)
    while balance_dataframe.loc[config.coin]['free'] == 0 :
        print(input("Your spot isn't enough."))
        # x = balance_dataframe.loc['ETH']['free'] # 錢包內是否有當初買入的現貨
    # free_coin_num = balance_dataframe.loc[config.coin]['free'] #暫時不用
    # open_price = pd.DataFrame(ftx.fetch_orders(symbol=spot_symbol))
    recent = pd.DataFrame(ftx.fetch_my_trades(symbol=spot_symbol,limit=1))
    # recent = pd.DataFrame(recent.tail(1)['info'])
    print(f'Spot check:True.')
    return recent['price'][0]



def perp_entry_price(perp_data):
    balance_dataframe = pd.DataFrame(perp_data)
    perp_status = balance_dataframe['info'][0]['side']
    while perp_status != 'sell':
        print(input("Your perp position is not correct."))
    print(f'Perp check:True.')
    return balance_dataframe['entryPrice'][0]



path = pathlib.Path().absolute()
auth_path = f'{path}/google_auth.json'
gc = pygsheets.authorize(service_file=auth_path)
sht = gc.open_by_url('https://docs.google.com/spreadsheets/d/1DoMWNaS_5DcCKQDfdoGMoLUUMDHChLpfNlTIvFw1hMU/edit#gid=1873229305')
# 列出清單
sht_list = sht.worksheets()
# 抓出歷史資金費率這一頁
funding_rate_history = sht.worksheet_by_title('歷史資金費率統計')
# 抓出需要的部分
df = funding_rate_history.get_as_df(start='B2',end='AC182')
df.set_index('幣種', inplace=True)
# df.to_csv('file_name.csv')  # 輸出CSV

# 檢查資金費率是否大於0
if percentage(df.loc[config.coin]['最近一次利率']) < 0:
    print("Currency funding rate is negative.")
    os._exit(0)


# 列出現貨和合約的市價，相減後得到開倉價差
spot_symbol = config.coin + "/USD"
perp_symbol = config.coin + "-PERP"
spot_ticker = ftx.fetch_ticker(spot_symbol)
perp_ticker = ftx.fetch_ticker(perp_symbol)
# open_price_gap = turn_to_decimal(perp_ticker['ask']-spot_ticker['ask'])
print(f"Your trade is long {spot_symbol}, short {perp_symbol}.")
# print(f'Your open price gap is {open_price_gap}')

# 買入現貨 做空合約
ftx.create_order(symbol=spot_symbol, side = 'buy', type = 'market', amount = config.coin_size)
ftx.create_order(symbol=perp_symbol, side = 'sell', type = 'market', amount = config.coin_size)

# 讓程式暫停Run，希望做到使用telegram輸入指令來讓程式繼續
input("Please enter your name: ")

# 檢查現貨合約是否都存在，順便抓開倉價格
spot_open_price = spot_entry_price(ftx.fetch_balance(),spot_symbol)
perp_open_price = perp_entry_price(ftx.fetch_positions()) ## 這個不會受到前後交易干擾，因為是直接抓持倉
# open_price_gap = perp_open_price - spot_open_price # 開倉價差
open_price_gap = perp_open_price - 0.1327465
close_price_gap = perp_ticker['ask']-spot_ticker['ask']


# 檢查關倉價差
gap = scie_to_decimal(open_price_gap - close_price_gap)
# gap_percent = (spot_ticker['ask']-spot_open_price)/spot_open_price + (perp_open_price - perp_ticker['ask'])/perp_open_price
gap_percent = turn_to_percentage((spot_ticker['ask']-0.1327465)/0.1327465 + (perp_open_price - perp_ticker['ask'])/perp_open_price)
print(f'Close price gap percentage:{gap_percent}')

# 暫停確定一下
input("Going to close position?(Y/N)")

# 賣出現貨 平倉合約
ftx.create_order(symbol=spot_symbol, side = 'sell', type = 'market', amount = config.coin_size)
ftx.create_order(symbol=perp_symbol, side = 'buy', type = 'market', amount = config.coin_size)
print("Success.")






