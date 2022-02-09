from __future__ import (absolute_import, division, print_function, unicode_literals)

from backtrader_plotting         import Bokeh
from backtrader_plotting.schemes import Blackly

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time

""" The purpose of this file is to compare the returns of investing in individual stocks vs the S&P 500"""


TEN_THOUSAND          = 10000
BTCUSD_DECIMAL_PLACES = 5

BTC_USD_1DAY_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN     = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"

AAPL_1DAY_ALL = "historical_data/stocks/AAPL.csv"
MSFT_1DAY_ALL = "historical_data/stocks/MSFT.csv"
GOOG_1DAY_ALL = "historical_data/stocks/GOOG.csv"
MCD_1DAY_ALL  = "historical_data/stocks/MCD.csv"
PG_1DAY_ALL   = "historical_data/stocks/PG.csv"
WMT_1DAY_ALL  = "historical_data/stocks/WMT.csv"
CSCO_1DAY_ALL = "historical_data/stocks/CSCO.csv"
KO_1DAY_ALL   = "historical_data/stocks/KO.csv"
DIS_1DAY_ALL  = "historical_data/stocks/DIS.csv"
BA_1DAY_ALL   = "historical_data/stocks/BA.csv"

SPY_1DAY_ALL = "historical_data/stocks/SPY.csv"


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"



class BuyAndHoldMultiAssetPaycheck(bt.Strategy):
    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def __init__(self) -> None:
        self.start_cash          = 0
        self.start_value         = 0
        self.total_cash_invested = 0

        self.next_paycheck_date  = None
        self.time_period         = None

        self.paycheck_amount = 10000
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
        print(f"[{date} {minutes}]")
        return

    def payday(self) -> None:
        if self.data.datetime.date() > self.next_paycheck_date:
            self.next_paycheck_date = self.data.datetime.date() + datetime.timedelta(14)
            self.broker.add_cash(self.paycheck_amount)
        return

    def start(self) -> None:
        self.start_cash  = self.broker.get_cash()
        return

    def next(self) -> None:
        self.print_ohlc()

        if self.next_paycheck_date is None:
            self.next_paycheck_date = self.data.datetime.date() + datetime.timedelta(14)

        for idx, datafeed in enumerate(self.datas):
            try:
                datafeed.close[idx]
            except:
                break

            num_stocks = (1 / len(self.datas)) * 0.90
            quantity_to_buy = int((self.broker.get_cash() / datafeed.close[idx]) * num_stocks) # allocate the same money to every stock

            if quantity_to_buy >= 1:
                self.buy(data=datafeed, size=quantity_to_buy, exectype=bt.Order.Market)

        self.payday()
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                self.total_cash_invested += order.executed.value
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
    
    df_msft = pd.read_csv(MSFT_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_goog = pd.read_csv(GOOG_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_pg   = pd.read_csv(PG_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_mcd  = pd.read_csv(MCD_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_aapl = pd.read_csv(AAPL_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    
    df_wmt  = pd.read_csv(WMT_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_csco = pd.read_csv(CSCO_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_ko   = pd.read_csv(KO_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_dis  = pd.read_csv(DIS_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df_ba   = pd.read_csv(BA_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    # df_spy  = pd.read_csv(SPY_1DAY_ALL, usecols=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

    df_msft['Date'] = pd.to_datetime(df_msft['Date']).dt.tz_localize(None)
    df_goog['Date'] = pd.to_datetime(df_goog['Date']).dt.tz_localize(None)
    df_pg['Date']   = pd.to_datetime(df_pg['Date']).dt.tz_localize(None)
    df_mcd['Date']  = pd.to_datetime(df_mcd['Date']).dt.tz_localize(None)
    df_aapl['Date'] = pd.to_datetime(df_aapl['Date']).dt.tz_localize(None)

    df_wmt['Date'] = pd.to_datetime(df_wmt['Date']).dt.tz_localize(None)
    df_csco['Date'] = pd.to_datetime(df_csco['Date']).dt.tz_localize(None)
    df_ko['Date'] = pd.to_datetime(df_ko['Date']).dt.tz_localize(None)
    df_dis['Date'] = pd.to_datetime(df_dis['Date']).dt.tz_localize(None)
    df_ba['Date'] = pd.to_datetime(df_ba['Date']).dt.tz_localize(None)
    # df_spy['Date'] = pd.to_datetime(df_spy['Date']).dt.tz_localize(None)

    df_msft.set_index('Date', inplace=True)
    df_goog.set_index('Date', inplace=True)
    df_pg.set_index('Date', inplace=True)
    df_mcd.set_index('Date', inplace=True)
    df_aapl.set_index('Date', inplace=True)

    df_wmt.set_index('Date', inplace=True)
    df_csco.set_index('Date', inplace=True)
    df_ko.set_index('Date', inplace=True)
    df_dis.set_index('Date', inplace=True)
    df_ba.set_index('Date', inplace=True)
    # df_spy.set_index('Date', inplace=True)    

    start_date = datetime.datetime(2004, 8, 19)
    end_date   = datetime.datetime(2022, 1, 1)
    
    data_msft = bt.feeds.PandasData(dataname=df_msft, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_goog = bt.feeds.PandasData(dataname=df_goog, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_pg   = bt.feeds.PandasData(dataname=df_pg, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_mcd  = bt.feeds.PandasData(dataname=df_mcd, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_aapl = bt.feeds.PandasData(dataname=df_aapl, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)

    data_wmt   = bt.feeds.PandasData(dataname=df_wmt, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_csco = bt.feeds.PandasData(dataname=df_csco, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_ko = bt.feeds.PandasData(dataname=df_ko, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_dis = bt.feeds.PandasData(dataname=df_dis, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    data_ba = bt.feeds.PandasData(dataname=df_ba, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)
    # data_spy = bt.feeds.PandasData(dataname=df_spy, timeframe=bt.TimeFrame.Days, fromdate=start_date, todate=end_date)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)

    cerebro.adddata(data_msft, name="MSFT")
    cerebro.adddata(data_goog, name="GOOG")
    cerebro.adddata(data_pg, name="PG")
    cerebro.adddata(data_mcd, name="MCD")
    cerebro.adddata(data_aapl, name="AAPL")

    cerebro.adddata(data_wmt, name="WMT")
    cerebro.adddata(data_csco, name="CSCO")
    cerebro.adddata(data_ko, name="KO")
    cerebro.adddata(data_dis, name="DIS")
    cerebro.adddata(data_ba, name="BA")

    # cerebro.adddata(data_spy, name="SPY")
    
    cerebro.addstrategy(BuyAndHoldMultiAssetPaycheck)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)

    print()
    print("^^^^ STARTING THE BACKTEST ^^^^^")
    print(f"*** Testing period: {start_date} - {end_date} ***")
    print()

    cerebro.run()

    b = Bokeh(style='bar', filename='backtest_results/buy_and_hold_multi_asset_paycheck.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)



"""
(2004, 8, 19) -> (2022, 1, 1)

    Stocks Used: AAPL, MSFT, GOOG, MCD, PG
        ^^^^ FINISHED BACKTESTING ^^^^^
        ##########################################

        Time period:           6344 days, 0:00:00
        Total Profit:          $20,053,828.500000
        ROI:                   974.80%
        Start Portfolio Value: $10,000.000000
        Total cash invested:   $2,057,228.910000
        Final Portfolio Value: $22,111,057.410000
        ##########################################

    Stocks Used: S&P 500
        ^^^^ FINISHED BACKTESTING ^^^^^
        ##########################################

        Time period:           6344 days, 0:00:00
        Total Profit:          $3,950,161.870000
        ROI:                   191.98%
        Start Portfolio Value: $10,000.000000
        Total cash invested:   $2,057,537.280000
        Final Portfolio Value: $6,007,699.150000
        ##########################################

"""