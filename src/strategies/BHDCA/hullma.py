from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly
from pprint                      import pprint

import pandas     as pd
import backtrader as bt

import datetime
import os
import sys

BTCUSD_DECIMAL_PLACES = 5
TEN_THOUSAND          = 10000
BTC_USD_1DAY_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN     = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"


class HullMA(bt.Strategy):
    def __init__(self) -> None:
        # day values
        self.hullma = bt.indicators.HullMovingAverage(self.datas[1], period=20)
        
        self.start_cash = 0
        self.start_value = 0
        self.prenext_count = 1
        self.order = None
        return

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]

        if isinstance(dt, float):
            dt = bt.num2date(dt)

        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def money_format(self, money: float) -> str:
        return "${:,.6f}".format(money)

    def print_ohlc(self) -> None:
        date = self.data.datetime.date()
        minutes = self.datas[0].datetime.time(0)
        open = self.money_format(self.data.open[0])
        high = self.money_format(self.data.high[0])
        low = self.money_format(self.data.low[0])
        close = self.money_format(self.data.close[0])
        print(
            f"[{date} {minutes}] Open: {open}, High: {high}, Low: {low}, Close: {close}\r", end='')
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: {:,.8f} Price: {:,.8f}, Cost: {:,.8f}, Comm {:,.8f}'.format(
                    order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            elif order.issell():
                self.log('SELL EXECUTED, Size: {:,.8f} Price: {:,.8f}, Cost: {:,.8f}, Comm {:,.8f}'.format(
                    order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                self.order = None
        elif order.status in [order.Canceled]:
            # if the sell was canceled, that means a safety order was filled and its time to put in a new updated take profit order.
            self.log(f'ORDER CANCELED: Size: {order.size}')
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (
                order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            print()
            print("Cash:", self.broker.get_cash())
            print("Value", self.broker.get_value())
            print()
            print(order)
            print()
            # sys.exit()
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (
                order.size, order.price, order.value, order.comm))
            print()
            print(order)
            print()
            sys.exit()
        else:
            self.log("ORDER UNKNOWN: SOMETHNG WENT WRONG!")
            print()
            print(order)
            print()
            sys.exit()
        return

    def notify_trade(self, trade: bt.trade.Trade) -> None:
        if trade.isclosed:
            self.log('TRADE COMPLETE, GROSS %.6f, NET %.6f, Size: %.6f' %
                     (trade.pnl, trade.pnlcomm, trade.size))

            # if trade.pnl <= 0 or trade.pnlcomm <= 0:
            #     print(trade.pnl, trade.pnlcomm)
            #     print()
            #     print(trade)
            #     print()
        return

    def prenext(self) -> None:
        print(
            f"Prenext: {self.prenext_count} \\ {self.prenext_total} {round((self.prenext_count/self.prenext_total)*100)}%\r", end='')
        self.prenext_count += 1
        return

    def next(self) -> None:
        self.print_ohlc()
        if self.hullma[0] - self.hullma[-1] > 0 and self.order is None:
            base_order_size = (self.broker.get_cash() / self.data.close[0]) * 0.98
            self.order = self.buy(size=base_order_size, exectype=bt.Order.Market)
        elif self.hullma[0] - self.hullma[-1] < 0 and self.order is not None:
            self.sell(size=self.position.size, exectype=bt.Order.Market)
        return

    def start(self) -> None:
        self.prenext_total = max(self._minperiods) * 60 * 24  # number of minutes in 200 days
        self.time_period = self.datas[0].p.todate - self.datas[0].p.fromdate
        self.start_cash = self.broker.get_cash()
        self.start_value = self.broker.get_value()
        return

    def stop(self) -> None:
        total_value = self.broker.get_value()
        profit = total_value - self.start_cash
        roi = ((total_value / self.start_cash) - 1.0) * 100
        roi = '{:.2f}%'.format(roi)

        profit = self.money_format(round(profit, 2))
        self.start_value = self.money_format(round(self.start_value, 2))
        total_value = self.money_format(round(total_value, 2))

        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print("##########################################")

        print()
        print(f"Time period:           {self.time_period}")
        print(f"Total Profit:          {profit}")
        print(f"ROI:                   {roi}")
        print(f"Start Portfolio Value: {self.start_value}")
        print(f"Final Portfolio Value: {total_value}")
        print("##########################################")
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
        start_date = datetime.datetime(year=2019, month=7, day=1, hour=0, minute=1)
        end_date   = datetime.datetime(year=2019, month=11, day=19, hour=0, minute=1)
    elif period == 4:
        # period 4: (7/1/2017 - 11/19/2017)
        start_date = datetime.datetime(year=2017, month=7, day=1, hour=0, minute=1)
        end_date   = datetime.datetime(year=2017, month=11, day=19, hour=0, minute=1)        
    elif period == 5:
        # period 5: (1/28/21 - 4/15/21)
        start_date = datetime.datetime(year=2021, month=1, day=28, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=4, day=15, hour=0, minute=1)
    elif period == 6:
        # period 6: (7/20/2021 -> 9/5/2021)
        start_date = datetime.datetime(year=2021, month=7, day=20, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=9, day=5, hour=0, minute=1)
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

    start_date, end_date = get_period(9)
    start_date -= datetime.timedelta(days=20) # time required to process the 200 day simple moving average

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
    
    cerebro.addstrategy(HullMA)

    cerebro.addindicator(bt.indicators.HullMovingAverage, period=20)

    print()
    print("^^^^ STARTING THE BACKTEST ^^^^^")
    print()

    cerebro.run()

    b = Bokeh(style='bar', filename='backtest_results/HullMA.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
