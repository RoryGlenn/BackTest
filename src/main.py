# https://www.youtube.com/watch?v=5VU3CJMuk0w

# To get free crypto data
# https://www.CryptoDataDownload.com


# Backtrader documentation on custom CSV files
# https://www.backtrader.com/docu/datafeed/

from strategies.DCA3C.dca3c_strategy import DCA3C
from strategies.DCA3C.dca3c_strategy import DCA
from strategies.DCA3C.dca_dynamic    import DCADynamic

from strategies.DCA3C.buy_and_hold   import BuyAndHold
from observers.stop_take             import SLTPTracking

from backtrader_plotting         import Bokeh, OptBrowser
from backtrader_plotting.schemes import Blackly, Tradimo


import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time

STARTING_CASH       = 1000000

BTC_USD_2017        = "historical_data/BTCUSD/Bitstamp_BTCUSD_2017_minute.csv"
BTC_USD_2018        = "historical_data/BTCUSD/Bitstamp_BTCUSD_2018_minute.csv"
BTC_USD_2018_SMALL  = "historical_data/BTCUSD/Bitstamp_BTCUSD_2018_minute_small.csv"
BTC_USD_ALL         = "historical_data/gemini/gemini_BTCUSD_1min_all.csv"

ORACLE              = "historical_data/oracle.csv"
BNGO                = "historical_data/BNGO.csv"

def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"


def oracle() -> None:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(ORACLE)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    # ORACLE
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(1995, 1, 3),
                               todate=datetime.datetime(2014, 12, 31))

    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)

    cerebro.run()
    cerebro.plot(style='candlestick', numfigs=1,
                    barup='green', bardown='red',
                    barupfill=True, bardownfill=True,
                    volup='green', voldown='red', voltrans=100.0, voloverlay=False)
    return


def bngo() -> None:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df         = pd.read_csv(BNGO)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    # BNGO
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(2018, 8, 21),
                               todate=datetime.datetime(2022, 1, 20))
    cerebro.adddata(data, name="BNGO")
    cerebro.addstrategy(DCA3C)
    cerebro.run()

    b = Bokeh(style='bar', filename='backtest_results/bngo_backtest_result.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    return


def btc_2018() -> None:
    start_time = time.time()
    
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(BTC_USD_ALL, 
                     low_memory=False,
                    #  usecols=['date', 'symbol', 'open', 'high', 'low', 'close', 'Volume USD'],
                     usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'],
                     parse_dates=True,
                     skiprows=1)
    
    # reverse the data
    df = df[::-1] 

    # rename the columns 
    # df.rename(columns={'date':'Date', 'symbol':'Symbol', 'open':'Open', 'high':'High', 'low':'Low', 'close':'Close', "Volume USD": 'Volume'}, inplace=True)

    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    print(df)

    # BTC 2018
    data = bt.feeds.PandasData(dataname=df,
                                timeframe=bt.TimeFrame.Minutes,
                                compression=1,
                                openinterest=None,

                                # for testing small timeframes
                                # fromdate=datetime.datetime(year=2018, month=1, day=1, hour=0, minute=1),
                                # todate=datetime.datetime(year=2018, month=2, day=1, hour=0, minute=1)
                                
                                # for testing the entire timeframe
                                fromdate=datetime.datetime(year=2015, month=10, day=8, hour=13, minute=41),
                                todate=datetime.datetime(year=2016, month=12, day=31, hour=23, minute=59)
                            )

    cerebro.adddata(data, name='BTC/USD-ALL') # adding a name while using bokeh will avoid plotting error
    # cerebro.resampledata(data, name='BTC/USD-2018', timeframe=bt.TimeFrame.Days)
    cerebro.addstrategy(DCA3C)
    # cerebro.addstrategy(BuyAndHold)
    
    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    b = Bokeh(style='bar', filename='backtest_results/btc_2018_backtest_result.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    return



if __name__ == '__main__':
    os.system("cls")
    os.system("color")

    # oracle()
    # bngo()
    btc_2018()

"""
('target_profit_percent',        0.5),


^^^^ FINISHED BACKTESTING ^^^^^

Time period:           364 days, 23:59:00
Total Profit:          $85,208.110000
ROI:                   8.52%
Start Portfolio Value: $1,000,000.000000
Final Portfolio Value: $1,085,208.109400
Time elapsed: 9 minutes 4 seconds


####################################################
('target_profit_percent',        1),

^^^^ FINISHED BACKTESTING ^^^^^

Time period:           364 days, 23:59:00
Total Profit:          $103,891.750000
ROI:                   10.39%
Start Portfolio Value: $1,000,000.000000
Final Portfolio Value: $1,103,891.752443
Time elapsed: 8 minutes 56 seconds

"""
