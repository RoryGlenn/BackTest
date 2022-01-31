from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly

from bhdca        import BHDCA
from buy_and_hold import BuyAndHold
from dca3c        import DCA3C

import backtrader as bt
import pandas     as pd

import datetime
import os
import time
import sys

from min_max import MinMax


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
    start_time = time.time()

    start_date = datetime.datetime(year=2021, month=1,  day=5,  hour=0, minute=0)
    end_date   = datetime.datetime(year=2021, month=12, day=31, hour=23, minute=59)

    df = pd.read_csv(BTC_USD_1MIN_ALL, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1) # read in the data
    # df = pd.read_csv(BTC_USD_1DAY_ALL, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1) # read in the data
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



"""

    ^^^^ FINISHED BACKTESTING ^^^^^
    ##########################################
    target_profit_percent:          1
    trail_percent:                  0.002
    safety_orders_max:              15
    safety_orders_active_max:       15
    safety_order_volume_scale:      1.2
    safety_order_step_scale:        1.16
    safety_order_price_deviation:   1.0
    base_order_size_usd:            20
    safety_order_sizes_usd:         216.0 - 256.0

    Time period:           564 days, 23:59:00
    Total Profit:          $7,517.100000
    ROI:                   75.17%
    Start Portfolio Value: $10,000.000000
    Final Portfolio Value: $17,517.100000
    ##########################################
    Time elapsed: 7 minutes 16 seconds


NOW FOR MY SECOND TRICK, I WILL UP THE BASE ORDER PRICE TO $250 AND RUN IT AGAIN WITH THE SAME SETTINGS!

    ^^^^ FINISHED BACKTESTING ^^^^^
    ##########################################
    target_profit_percent:          1
    trail_percent:                  0.002
    safety_orders_max:              15
    safety_orders_active_max:       15
    safety_order_volume_scale:      1.2
    safety_order_step_scale:        1.16
    safety_order_price_deviation:   1.0
    base_order_size_usd:            250
    safety_order_sizes_usd:         214.0 - 256.0

    Time period:           564 days, 23:59:00
    Total Profit:          $7,971.150000
    ROI:                   79.71%
    Start Portfolio Value: $10,000.000000
    Final Portfolio Value: $17,971.150000
    ##########################################
    Time elapsed: 7 minutes 5 seconds


NOTICE A 4.54% difference!

"""