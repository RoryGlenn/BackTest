from bhdca import BHDCA

from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly

import backtrader as bt
import pandas     as pd

import datetime
import os
import time


TEN_THOUSAND      = 10000
FILE              = ""
BTC_USD_1DAY_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"



def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"


def bhdca() -> None:
    start_time = time.time()

    FILE1      = BTC_USD_2021_1MIN
    start_date = datetime.datetime(year=2021, month=1,  day=1,  hour=0, minute=0)
    end_date   = datetime.datetime(year=2021, month=12, day=31, hour=23, minute=59)

    df = pd.read_csv(FILE1, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1)
    df = df[::-1] # reverse the data

    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

    df.set_index('Date', inplace=True)

    # BTC/USD
    data_minute = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, fromdate=start_date, todate=end_date)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data_minute, name='BTCUSD_MINUTE') # adding a name while using bokeh will avoid plotting error
    cerebro.resampledata(data_minute, timeframe=bt.TimeFrame.Days, compression=1, name="BTCUSD_DAY")
    cerebro.addstrategy(BHDCA)

    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    b = Bokeh(style='bar', filename='backtest_results/BHDCA.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    return



if __name__ == '__main__':
    os.system("cls")
    bhdca()
