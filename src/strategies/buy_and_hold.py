from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time

TEN_THOUSAND          = 10000
BTC_USD_1DAY_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN     = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"

BTCUSD_DECIMAL_PLACES = 5

p              = None
period_results = dict()


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"



class BuyAndHold(bt.Strategy):
    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def __init__(self) -> None:
        self.start_cash  = 0
        self.current_cash = 0
        self.start_value = 0
        self.time_period = None
        self.order       = None
        return

    def get_elapsed_time(self, start_time: float) -> str:
        end_time     = time.time()
        elapsed_time = round(end_time - start_time)
        minutes      = elapsed_time // 60
        seconds      = elapsed_time % 60
        return f"{minutes} minutes {seconds} seconds"

    def money_format(self, money: float) -> str:
        return "${:,.6f}".format(money)

    def print_ohlc(self) -> None:
        date    = self.data.datetime.date()
        minutes = self.datas[0].datetime.time(0)
        open    = self.money_format(self.data.open[0])
        high    = self.money_format(self.data.high[0])
        low     = self.money_format(self.data.low[0])
        close   = self.money_format(self.data.close[0])
        print(f"[{date} {minutes}] Open: {open}, High: {high}, Low: {low}, Close: {close}\r", end='')
        return

    def start(self) -> None:
        self.start_cash  = self.broker.get_cash()
        self.current_cash = self.broker.get_cash()
        return

    def nextstart(self) -> None:
        return

    def next(self) -> None:
        self.print_ohlc()

        if not self.position:
            quantity_to_buy = self.start_cash / self.data.close[0]
            quantity_to_buy = quantity_to_buy * 0.99
            self.order      = self.buy(size=quantity_to_buy, exectype=bt.Order.Market)        
        return

    def notify_cashvalue(self, cash, value) -> None:
        print("cash: ", cash)
        print("self.current_cash: ", self.current_cash)
        
        self.current_cash = cash
        return


    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            elif order.issell():
                self.log('SELL EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Canceled]:
            self.log(f'ORDER CANCELED: Size: {order.size}')
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            sys.exit()
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.size, order.price, order.value, order.comm))
            sys.exit()
        else:
            sys.exit()
        return

    def start(self) -> None:
        self.time_period = self.datas[0].p.todate - self.datas[0].p.fromdate
        self.start_cash  = self.broker.get_cash()
        self.start_value = self.broker.get_value()
        return


    def stop(self) -> None:
        global period_results

        total_value = self.broker.get_value()
        profit      = total_value - self.start_cash
        roi         = ((total_value / self.start_cash) - 1.0) * 100
        roi         = '{:.2f}%'.format(roi)

        profit           = self.money_format(round(profit, 2))
        self.start_value = self.money_format(round(self.start_value, 2))
        total_value      = self.money_format(round(total_value, 2))

        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print("##########################################")

        print(f"*** Period {p} results ***")

        print()
        print(f"Time period:           {self.time_period}")
        print(f"Total Profit:          {profit}")
        print(f"ROI:                   {roi}")
        print(f"Start Portfolio Value: {self.start_value}")
        print(f"Final Portfolio Value: {total_value}")
        print("##########################################")
        
        period_results[p] = roi
        return


def get_period(period: int) -> datetime:
    start_date = None
    end_date   = None

    if period == 1:
        # period 1: (4/14/2021 - 7/21/21)
        start_date = datetime.datetime(year=2021, month=4, day=14, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=7, day=21, hour=0, minute=1)    
    elif period == 2:
        # period 2: (1/7/2018 - 4/1/2018)
        start_date = datetime.datetime(year=2018, month=1, day=7, hour=0, minute=1)
        end_date   = datetime.datetime(year=2018, month=4, day=1, hour=0, minute=1)
    elif period == 3:
        # period 3: (7/1/2019 - 11/19/2019)
        start_date = datetime.datetime(year=2019, month=7,  day=1,  hour=0, minute=1)
        end_date   = datetime.datetime(year=2019, month=11, day=19, hour=0, minute=1)
    elif period == 4:
        # period 4: (7/1/2017 - 11/19/2017)
        start_date = datetime.datetime(year=2017, month=7,  day=1,  hour=0, minute=1)
        end_date   = datetime.datetime(year=2017, month=11, day=19, hour=0, minute=1)        
    elif period == 5:
        # period 5: (1/28/21 - 4/15/21)
        start_date = datetime.datetime(year=2021, month=1, day=28, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=4, day=15, hour=0, minute=1)
    elif period == 6:
        # period 6: (7/20/2021 -> 9/5/2021)
        start_date = datetime.datetime(year=2021, month=7, day=20, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=9, day=5,  hour=0, minute=1)
    elif period == 7:
        # period 7: 5/9/21 -> 9/9/21
        start_date = datetime.datetime(year=2021, month=5, day=9, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=9, day=9, hour=0, minute=1)
    elif period == 8:
        # period 8: 1/1/2019 -> 5/5/2019
        start_date = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1)
        end_date   = datetime.datetime(year=2019, month=5, day=1, hour=0, minute=1)
    elif period == 9:
        # period 9: 1/1/2019 -> 4/1/19
        start_date = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1)
        end_date   = datetime.datetime(year=2019, month=4, day=1, hour=0, minute=1)
    elif period == 10:
        # period 10: 1/1/2016 -> 1/26/2022
        start_date = datetime.datetime(year=2016, month=1, day=1, hour=0, minute=1)
        end_date   = datetime.datetime(year=2022, month=1, day=1, hour=0, minute=1)
    else:
        print("invalid period")
        sys.exit()
    return start_date, end_date



if __name__ == '__main__':
    os.system('cls')
    
    period_results = dict()

    for period in range(1, 11): # PERIOD 1-10
        start_date, end_date = get_period(period)

        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str   = end_date.strftime(  "%Y-%m-%d %H:%M:%S")

        df = pd.read_csv(BTC_USD_1MIN_ALL, usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'], skiprows=1) # read in the data
        df = df[::-1] # reverse the data

        # to improve start up speed, drop all data outside of testing timeframe
        df = df.drop(df[df['Date'] < start_date_str].index)
        df = df.drop(df[df['Date'] > end_date_str].index)

        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        df.set_index('Date', inplace=True)

        print(df)

        data = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Minutes, fromdate=start_date, todate=end_date)

        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(TEN_THOUSAND)
        cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

        cerebro.adddata(data, name='BTCUSD_MINUTE') # adding a name while using bokeh will avoid plotting error
        cerebro.resampledata(data, timeframe=bt.TimeFrame.Days, compression=1, name="BTCUSD_DAY")
        
        cerebro.addstrategy(BuyAndHold)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio)

        p = period

        print()
        print("^^^^ STARTING THE BACKTEST ^^^^^")
        print(f"*** Testing period {p} ***")
        print()

        cerebro.run()

        # b = Bokeh(style='bar', filename='backtest_results/BuyAndHold.html', output_mode='show', scheme=Blackly())
        # cerebro.plot(b)

    for period, roi in period_results.items():
        print(f"period: {period}, roi: {roi}")


"""
STARTING CASH = $10,000.0

TIME PERIODS:
    periods 1-3: bear markets
    periods 4-6: bull markets
    periods 7-9: sideways/neutral markets
    period  10:  all

        period 1: 4/14/2021 - 7/21/2021  -52.46%
        period 2: 1/7/2018  - 4/1/2018   -53.06%
        period 3: 7/1/2019  - 11/19/2019 -24.76%

        period 4: 7/1/2017  - 11/19/2017 207.17%
        period 5: 1/28/2021 - 4/15/2021  83.82%
        period 6: 7/20/2021 - 9/5/2021   54.83%

        period 7: 5/9/2021  - 9/9/2021 -17.48%
        period 8: 1/1/2019  - 5/5/2019  35.03%
        period 9: 1/1/2019  - 4/1/2019   5.13%

        period 10: 1/1/2016 - 1/1/2022 10422.19%


"""