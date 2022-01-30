from strategies.DCA3C.dca3c_strategy import DCA3C

from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly

import backtrader as bt
import pandas     as pd

import datetime
import os
import time

TEN_THOUSAND = 10000
FILE         = ""
BTC_USD_1DAY_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"



def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"


def btc_bear_bull() -> None:
    start_time = time.time()

    #############################################################################
    # period 1 ALT: (4/14/2021 - 7/21/21)
    FILE1       = BTC_USD_2021_1MIN
    start_date1 = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1)
    end_date1   = datetime.datetime(year=2021, month=4, day=1, hour=0, minute=1)

    # Day values
    FILE2       = BTC_USD_1DAY_ALL
    start_date2 = datetime.datetime(year=2015, month=10, day=8)
    end_date2   = datetime.datetime(year=2022, month=1, day=28)
    #############################################################################

    df_minute = pd.read_csv(FILE1, low_memory=False, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1)
    df_day    = pd.read_csv(FILE2, low_memory=False, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1)

    # reverse the data
    df_minute = df_minute[::-1]
    df_day    = df_day[::-1]

    df_minute['Date'] = pd.to_datetime(df_minute['Date']).dt.tz_localize(None)
    df_day['Date']    = pd.to_datetime(df_day['Date']).dt.tz_localize(None)

    df_minute.set_index('Date', inplace=True)
    df_day.set_index('Date',    inplace=True)

    # BTC/USD
    data_minute = bt.feeds.PandasData(dataname=df_minute, timeframe=bt.TimeFrame.Minutes, fromdate=start_date1, todate=end_date1)
    data_day    = bt.feeds.PandasData(dataname=df_day, timeframe=bt.TimeFrame.Days, fromdate=start_date2, todate=end_date2)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data_minute, name='BTCUSD_MINUTE') # adding a name while using bokeh will avoid plotting error
    cerebro.adddata(data_day,    name='BTCUSD_DAY')    # adding a name while using bokeh will avoid plotting error
    cerebro.addstrategy(DCA3C)

    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    b = Bokeh(style='bar', filename='backtest_results/testgraph.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    return



def btc_bear_bull_resample() -> None:
    start_time = time.time()

    #############################################################################
    # period 1 ALT: (4/14/2021 - 7/21/21)
    FILE1       = BTC_USD_2021_1MIN
    start_date1 = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1)
    end_date1   = datetime.datetime(year=2021, month=12, day=30, hour=0, minute=1)

    df_minute = pd.read_csv(FILE1, low_memory=False, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1)

    # reverse the data
    df_minute = df_minute[::-1]

    df_minute['Date'] = pd.to_datetime(df_minute['Date']).dt.tz_localize(None)

    df_minute.set_index('Date', inplace=True)

    # BTC/USD
    data_minute = bt.feeds.PandasData(dataname=df_minute, timeframe=bt.TimeFrame.Minutes, fromdate=start_date1, todate=end_date1)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data_minute, name='BTCUSD_MINUTE') # adding a name while using bokeh will avoid plotting error
    cerebro.resampledata(data_minute, timeframe=bt.TimeFrame.Days, compression=1, name="BTCUSD_DAY")
    cerebro.addstrategy(DCA3C)

    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    b = Bokeh(style='bar', filename='backtest_results/testgraph.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    return



if __name__ == '__main__':
    os.system("cls")
    btc_bear_bull_resample()
