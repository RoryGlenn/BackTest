from __future__ import (absolute_import, division, print_function, unicode_literals)




from bhdca import BHDCA

from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly
from pprint                      import pprint

import pandas     as pd
import backtrader as bt

import datetime
import os
import time


BTC_USD_1DAY_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"


class MinMax(bt.Strategy):
    def __init__(self) -> None:
        self.time_period = None
        self.low_high_perc_max = list() # day values
        self.high_low_perc_max = list()
        self.low_high_dict     = dict()
        self.high_low_dict     = dict()

        self.hullma_20_day = bt.indicators.HullMovingAverage(self.datas[0],   period=20)
        self.prev_hullma = None
        return

    def money_format(self, money: float) -> str:
        return "${:,.6f}".format(money)

    def print_ohlc(self) -> None:
        date    = self.data.datetime.date()
        minutes = self.datas[0].datetime.time(0)
        open    = self.money_format(self.data.open[0])
        high    = self.money_format(self.data.high[0])
        low     = self.money_format(self.data.low[0])
        close   = self.money_format(self.data.close[0])
        print(f"[{date} {minutes}] Open: {open}, High: {high}, Low: {low}, Close: {close}")
        return

    def next(self) -> None:
        self.print_ohlc()

        date  = self.data.datetime.date()
        high  = self.data.high[0]
        low   = self.data.low[0]
        close = self.data.close[0]
        open  = self.data.open[0]

        # if the high was $40,000 and the low was $20,000, the movement from high to low was 50%
        high_to_low_percent = (low / high) * 100

        # if the low was $20,000 and the high was $40,000, the movement from low to high was 100%
        low_to_high_percent = (high / low) * 100

        self.high_low_dict[date] = high_to_low_percent
        self.low_high_dict[date] = low_to_high_percent

        date_str = date.strftime("%Y-%m-%d %H:%M:%S")

        if len(self.high_low_perc_max) == 0:
            self.high_low_perc_max.append(high_to_low_percent)
        # if len(self.low_high_perc_max) == 0:
        #     self.low_high_perc_max.append(low_to_high_percent)

        if close < open:
            # the price went down
            if high_to_low_percent < min(self.high_low_perc_max):
                self.high_low_dict[date_str] = high_to_low_percent
        
        # if close > open:
        #     # the price went up
        #     if low_to_high_percent >= max(self.low_high_perc_max):
        #         self.low_high_dict[date_str] = low_to_high_percent

        # HOW HIGH SHOULD THE HULL DIFF BE FOR US TO BUY?
        if self.prev_hullma is None:
            self.prev_hullma = self.hullma_20_day[0]
        
        hull_diff = self.hullma_20_day - self.prev_hullma # 0 is when its flat?
        print('hull_diff:', hull_diff)

        self.prev_hullma = self.hullma_20_day[0]
        return

    def start(self) -> None:
        self.time_period = self.datas[0].p.todate - self.datas[0].p.fromdate
        return

    def stop(self) -> None:
        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print()

        # figure out the max of both dictionaries
        # then calculate the average

        print("high to low percents")

        for key, value in self.high_low_dict.items():
            if value == min(self.high_low_dict.values()):
                _min = min(self.high_low_dict.values())
                print(key, round(_min))
                break

        print()
        
        # print("low to high percents")

        # for key, value in self.low_high_dict.items():
        #     if value == max(self.low_high_dict.values()):
        #         _max = max(self.low_high_dict.values())
        #         print(key, round(_max))
        #         break

        print()
        print(f"Time period: {self.time_period}")
        print()
        return


if __name__ == '__main__':
    os.system('cls')

    # start_date = datetime.datetime(year=2015, month=10,  day=9,  hour=4)
    start_date = datetime.datetime(year=2021, month=1,  day=1,  hour=4)
    end_date   = datetime.datetime(year=2022, month=1, day=28, hour=4)

    df = pd.read_csv(BTC_USD_1DAY_ALL, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1) # read in the data
    df = df[::-1] # reverse the data

    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str   = end_date.strftime(  "%Y-%m-%d %H:%M:%S")

    # to improve start up speed, drop all data outside of testing timeframe
    df = df.drop(df[df['Date'] < start_date_str].index)
    df = df.drop(df[df['Date'] > end_date_str].index)

    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

    df.set_index('Date', inplace=True)

    print(df)

    data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)

    cerebro = bt.Cerebro()
    # cerebro.broker.set_cash(1000)
    # cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data, name='BTCUSD_DAY') # adding a name while using bokeh will avoid plotting error
    cerebro.addstrategy(MinMax)        # [Day values = 87.65%]

    print()
    print("^^^^ STARTING THE BACKTEST ^^^^^")
    print()

    cerebro.run()

    b = Bokeh(style='bar', filename='backtest_results/BHDCA.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)