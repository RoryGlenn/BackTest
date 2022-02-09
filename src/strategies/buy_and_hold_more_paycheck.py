"""

buy_and_hold_more.py - Strategy attempts to simulate what would happen if we bought and held but instead of only doing that, 
we bought again when the price falls below an arbitrary threshold.
The strategy is similar to buy and hold but also similar to DCA because we will set specific price levels and quantities to buy at.


Every 2 weeks, we will receive a paycheck with an arbitrary amount.
We will store this money until the price dips below our theshold.

We will compare this result to a simple buy and hold approach where every 2 weeks, the paycheck is invested immediatly into the market.
"""


from __future__ import (absolute_import, division, print_function, unicode_literals)

from backtrader_plotting         import Bokeh
from backtrader_plotting.schemes import Blackly

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time


TEN_THOUSAND          = 10000
BTCUSD_DECIMAL_PLACES = 5

BTC_USD_1DAY_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN     = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"
SPY_1DAY_ALL          = "historical_data/stocks/SPY.csv"



def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"



class BuyAndHoldMorePaycheck(bt.Strategy):
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
        self.start_value = 0
        self.time_period = None
        self.order       = None
        self.total_cash_invested = 0

        self.next_paycheck_date = None
        self.has_paycheck = False


        self.current_price = None
        self.buy_more_thres_perc_10 = 10
        self.buy_more_thres_perc_20 = 20
        self.buy_more_thres_perc_30 = 30
        self.buy_more_thres_perc_40 = 40
        self.buy_more_thres_perc_50 = 50

        self.volume_step = 2 # 2x
        self.previous_volume = 0

        self.all_time_high = -1

        self.paycheck_amount = 1000

        self.dca = None

        self.bought_thes_prec_10 = False
        self.bought_thes_prec_20 = False
        self.bought_thes_prec_30 = False
        self.bought_thes_prec_40 = False
        self.bought_thes_prec_50 = False

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
        print(f"[{date} {minutes}] Open: {open}, High: {high}, Low: {low}, Close: {close}")
        return

    def payday(self) -> None:
        if self.data.datetime.date() > self.next_paycheck_date:
            self.next_paycheck_date = self.data.datetime.date() + datetime.timedelta(14)
            self.broker.add_cash(self.paycheck_amount)
            self.has_paycheck = True
        return

    def start(self) -> None:
        self.start_cash  = self.broker.get_cash()
        return

    def nextstart(self) -> None:
        self.next_paycheck_date = self.data.datetime.date() + datetime.timedelta(14)

        if not self.position:
            quantity_to_buy = int((self.start_cash / self.data.close[0]) * 0.99)
            self.order      = self.buy(size=quantity_to_buy, exectype=bt.Order.Market)
            self.total_cash_invested += quantity_to_buy * self.data.close[0]
        return

    def next(self) -> None:
        self.print_ohlc()
        
        if self.data.close[0] > self.all_time_high:
            self.all_time_high       = self.data.close[0]
            self.bought_thes_prec_10 = False
            self.bought_thes_prec_20 = False
            self.bought_thes_prec_30 = False
            self.bought_thes_prec_40 = False
        else:
            # how far is the current price from the all time high?
            distance_from_ath_ratio = round(((self.all_time_high / self.data.close[0]) - 1) * 100, 3)
            quantity_to_buy         = 0

            # if we have cash and the market dipped below the threshold, buy more!
            if distance_from_ath_ratio >= self.buy_more_thres_perc_10 and distance_from_ath_ratio < self.buy_more_thres_perc_20:
                if not self.bought_thes_prec_10:
                    quantity_to_buy = int((self.broker.get_cash() / self.data.close[0]) * 0.20)
                    self.bought_thes_prec_10 = True
            elif distance_from_ath_ratio >= self.buy_more_thres_perc_20 and distance_from_ath_ratio < self.buy_more_thres_perc_30:
                if not self.bought_thes_prec_20:
                    quantity_to_buy = int((self.broker.get_cash() / self.data.close[0]) * 0.40)
                    self.bought_thes_prec_20 = True
            elif distance_from_ath_ratio >= self.buy_more_thres_perc_30 and distance_from_ath_ratio < self.buy_more_thres_perc_40:
                if not self.bought_thes_prec_30:
                    quantity_to_buy = int((self.broker.get_cash() / self.data.close[0]) * 0.60)
                    self.bought_thes_prec_30 = True
            elif distance_from_ath_ratio >= self.buy_more_thres_perc_40 and distance_from_ath_ratio < self.buy_more_thres_perc_50:
                if not self.bought_thes_prec_40:
                    quantity_to_buy = int((self.broker.get_cash() / self.data.close[0]) * 0.80)
                    self.bought_thes_prec_40 = True
            elif distance_from_ath_ratio >= self.buy_more_thres_perc_50:
                quantity_to_buy = int((self.broker.get_cash() / self.data.close[0]) * 0.94)
            else:
                return

            # if we have enough money to buy at least 1 share
            if quantity_to_buy > 0:
                self.order = self.buy(size=quantity_to_buy, exectype=bt.Order.Market)
                self.total_cash_invested += quantity_to_buy * self.data.close[0]
        self.payday()
        return

    def notify_cashvalue(self, cash: float, value: float) -> None:
        if cash != self.broker.get_cash():
            print("cash: ", cash)
            print("self.broker.get_cash():", self.broker.get_cash())
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
            print()
            print(order)
            print(self.broker.get_cash())
            print(self.data.close[0])
            # sys.exit()
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
        total_value = self.broker.get_value()
        profit      = total_value - self.total_cash_invested
        roi         = ((total_value / self.total_cash_invested) - 1.0) * 100
        roi         = '{:.2f}%'.format(roi)

        profit              = self.money_format(round(profit, 2))
        start_value         = self.money_format(round(self.start_value, 2))
        total_value         = self.money_format(round(total_value, 2))
        total_cash_invested = self.money_format(round(self.total_cash_invested, 2))

        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print("##########################################")

        print()
        print(f"Time period:           {self.time_period}")
        print(f"Total Profit:          {profit}")
        print(f"ROI:                   {roi}")
        print(f"Start Portfolio Value: {start_value}")
        print(f"Total cash invested:   {total_cash_invested}")
        print(f"Final Portfolio Value: {total_value}")
        print("##########################################")
        return



if __name__ == '__main__':
    os.system('cls')
    
    df = pd.read_csv(SPY_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']) # read in the data

    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    start_date = datetime.datetime(1993, 1, 29)
    end_date   = datetime.datetime(2022, 2, 7)
    data       = bt.feeds.PandasData(dataname=df, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data, name='SPY_DAY') # adding a name while using bokeh will avoid plotting error
    
    cerebro.addstrategy(BuyAndHoldMorePaycheck)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)

    print()
    print("^^^^ STARTING THE BACKTEST ^^^^^")
    print(f"*** Testing period: {start_date} - {end_date} ***")
    print()

    cerebro.run()

    b = Bokeh(style='bar', filename='backtest_results/buy_and_hold_more.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)



"""

^^^^ FINISHED BACKTESTING ^^^^^
##########################################

Time period:           10601 days, 0:00:00
Total Profit:          $1,118,643.430000
ROI:                   259.22%
Start Portfolio Value: $10,000.000000
Total cash invested:   $431,542.400000
Final Portfolio Value: $1,550,185.830000
##########################################


"""