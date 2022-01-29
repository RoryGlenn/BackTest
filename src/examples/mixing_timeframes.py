# Indicators - mixing timeframes
# https://www.backtrader.com/blog/posts/2016-05-05-indicators-mixing-timeframes/indicators-mixing-timeframes/




from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
import backtrader.utils.flushfile
import pandas as pd


import datetime

BTC_USD_2021 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"



class St(bt.Strategy):
    params = dict(multi=True)

    def __init__(self):
        self.pp = pp = btind.PivotPoint(self.data1)
        pp.plotinfo.plot = False  # deactivate plotting

        if self.p.multi:
            pp1 = pp()  # couple the entire indicators
            self.sellsignal = self.data0.close < pp1.s1
        else:
            self.sellsignal = self.data0.close < pp.s1()

    def next(self):
        txt = ','.join(
            ['%04d' % len(self),
             '%04d' % len(self.data0),
             '%04d' % len(self.data1),
             self.data.datetime.date(0).isoformat(),
             '%.2f' % self.data0.close[0],
             '%.2f' % self.pp.s1[0],
             '%.2f' % self.sellsignal[0]])

        print(txt)


def runstrat():
    cerebro = bt.Cerebro()

    # small testing dates only
    start_date = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1)
    end_date   = datetime.datetime(year=2021, month=4, day=1, hour=0, minute=1)
    
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str   = end_date.strftime(  "%Y-%m-%d %H:%M:%S")

    df = pd.read_csv(BTC_USD_2021,
                     low_memory=False,
                     usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'],
                     parse_dates=True,
                     skiprows=1)
    
    # reverse the data
    df = df[::-1]

    # to improve start up speed, drop all data outside of testing timeframe
    df = df.drop(df[df['Date'] < start_date_str].index)
    df = df.drop(df[df['Date'] > end_date_str].index)

    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    print(df)

    # BTC/USD
    data = bt.feeds.PandasData(dataname=df, 
                            timeframe=bt.TimeFrame.Minutes,
                            fromdate=start_date,
                            todate=end_date)

    cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Days)
    cerebro.addstrategy(St, multi=True)
    cerebro.run(runonce=False) # didn't notice any difference when runonce=True
    cerebro.plot(style='bar')


if __name__ == '__main__':
    runstrat()
