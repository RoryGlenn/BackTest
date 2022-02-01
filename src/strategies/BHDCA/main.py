from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly

from bhdca        import BHDCA
from buy_and_hold import BuyAndHold
from dca3c        import DCA3C
from min_max      import MinMax

import backtrader as bt
import pandas     as pd

import datetime
import os
import time
import sys



TEN_THOUSAND      = 10000
BTC_USD_1DAY_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"


def bhdca() -> None:

    """
    
    Compare our results with the S%P500 8%.

    Can we make more than this in a year for every year?

    Repeat this for each strategy
        DCA
        HullMA
        Buy&Hold
        BHDCA
        anything else...
    
    """


    start_time = time.time()

    # period 1: (4/14/2021 - 7/21/21)
    start_date = datetime.datetime(year=2021, month=4, day=14, hour=0, minute=1)
    end_date   = datetime.datetime(year=2021, month=7, day=21, hour=0, minute=1)

    df = pd.read_csv(BTC_USD_1MIN_ALL, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1) # read in the data
    df = df[::-1] # reverse the data

    start_date -= datetime.timedelta(days=200) # time required to process the 200 day simple moving average

    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str   = end_date.strftime(  "%Y-%m-%d %H:%M:%S")

    # to improve start up speed, drop all data outside of testing timeframe
    df = df.drop(df[df['Date'] < start_date_str].index)
    df = df.drop(df[df['Date'] > end_date_str].index)

    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

    df.set_index('Date', inplace=True)

    print(df)

    data_minute = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, fromdate=start_date, todate=end_date)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data_minute, name='BTCUSD_MINUTE') # adding a name while using bokeh will avoid plotting error
    cerebro.resampledata(data_minute, timeframe=bt.TimeFrame.Days, compression=1, name="BTCUSD_DAY")
    
    cerebro.addstrategy(BHDCA)          # [Day values = 87.65%] [Minute values = 79.71%%]
    # cerebro.addstrategy(DCA3C)        # [Day values = 15.02%] [ ... ]
    # cerebro.addstrategy(BuyAndHold)   # [Day values = 58.71%] [Minute values = 192.33%] # this has to be wrong.... double check the minute values with the day values

    # adding analyzers
    cerebro.addindicator(bt.indicators.HullMovingAverage,   period=20)
    cerebro.addindicator(bt.indicators.MovingAverageSimple, period=200)

    print()
    print("^^^^ STARTING THE BACKTEST ^^^^^")
    print()

    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")
    print()

    b = Bokeh(style='bar', filename='backtest_results/BHDCA.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    return



if __name__ == '__main__':
    os.system("cls")
    bhdca()
