from strategies.DCA3C.dca3c_strategy import DCA
from strategies.DCA3C.dca3c_strategy import DCA3C
from strategies.DCA3C.dca_dynamic    import DCADynamic

from strategies.buy_and_hold         import BuyAndHold
from observers.stop_take             import SLTPTracking

from backtrader_plotting             import Bokeh,   OptBrowser
from backtrader_plotting.schemes     import Blackly, Tradimo

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time


ONE_MILLION  = 1000000
TEN_THOUSAND = 10000
ONE_THOUSAND = 1000

BTC_USD_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"
BTC_USD_2017 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2017_1min.csv"
BTC_USD_2018 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2018_1min.csv"
BTC_USD_2019 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2019_1min.csv"
BTC_USD_2020 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2020_1min.csv"
BTC_USD_2021 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
ORACLE       = "historical_data/stocks/oracle.csv"
BNGO         = "historical_data/stocks/BNGO.csv"
FILE         = ""


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"


def oracle() -> None:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(ONE_MILLION)

    df = pd.read_csv(ORACLE)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    # ORACLE
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(1995, 1, 3),
                               todate=datetime.datetime(2014, 12, 31))

    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)
    # cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Minutes, compression=1, _name="SharpeRatio")

    cerebro.run()
    cerebro.plot(style='candlestick', numfigs=1,
                    barup='green', bardown='red',
                    barupfill=True, bardownfill=True,
                    volup='green', voldown='red', voltrans=100.0, voloverlay=False)
    return


def bngo() -> None:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(ONE_MILLION)

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


def btc() -> None:
    start_time = time.time()

    # could there be a way to switch between DCA and lump sum investing?
    # if we are above the 200MA, lump sum invest. Buy/Sell according to the hull moving average
    # if we are below, DCA?


    """
        periods 1-3: bear markets
        periods 4-6: bull markets
        periods 7-9: sideways/neutral markets

    """

    # period 1: (4/14/2021 - 7/21/21)
    # FILE       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=4, day=14, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=7, day=21, hour=0, minute=1)

    # period 2: (1/7/2018 - 4/1/2018)
    # FILE       = BTC_USD_2018
    # start_date = datetime.datetime(year=2018, month=1, day=7, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2018, month=4, day=1, hour=0, minute=1)

    # period 3: (7/1/2019 - 11/19/2019)
    # FILE       = BTC_USD_2019
    # start_date = datetime.datetime(year=2019, month=7, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2019, month=11, day=19, hour=0, minute=1)

    # period 4: (7/1/2017 - 11/19/2017)
    # FILE       = BTC_USD_2017
    # start_date = datetime.datetime(year=2017, month=9, day=20, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2017, month=12, day=17, hour=0, minute=1)

    # period 5: (1/28/21 - 4/15/21)
    # FILE       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=1, day=28, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=4, day=15, hour=0, minute=1)

    # period 6: (7/20/2021 -> 9/5/2021)
    # FILE       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=7, day=20, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=9, day=5, hour=0, minute=1)

    # period 7: 5/9/21 -> 9/9/21
    FILE       = BTC_USD_2020
    start_date = datetime.datetime(year=2020, month=5, day=9, hour=0, minute=1)
    end_date   = datetime.datetime(year=2020, month=9, day=9, hour=0, minute=1)

    # period 8: 5/9/21 -> 9/9/21
    # FILE       = BTC_USD_2019
    # start_date = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2019, month=5, day=1, hour=0, minute=1)

    # period 9: 1/1/2019 -> 4/1/19
    # FILE       = BTC_USD_2019
    # start_date = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2019, month=4, day=1, hour=0, minute=1)


    ##############################################################################


    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str   = end_date.strftime("%Y-%m-%d %H:%M:%S")

    df = pd.read_csv(FILE,
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
    data = bt.feeds.PandasData(
                                dataname=df,
                                timeframe=bt.TimeFrame.Minutes,
                                fromdate=start_date,
                                todate=end_date)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data, name='BTC/USD-ALL') # adding a name while using bokeh will avoid plotting error
    # cerebro.addstrategy(DCA3C)
    cerebro.addstrategy(BuyAndHold)

    # adding analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.VWR,         timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.PeriodStats, timeframe=bt.TimeFrame.Minutes)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.SQN)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    b = Bokeh(style='bar',
              filename='backtest_results/Scalp20_period2.html',
              output_mode='show',
              scheme=Blackly())
    cerebro.plot(b)
    return



if __name__ == '__main__':
    os.system("cls")
    os.system("color")

    # dca = DCA( entry_price_usd=63661.29,
    #             target_profit_percent=1,
    #             safety_orders_max=7,
    #             safety_orders_active_max=7,
    #             safety_order_volume_scale=2.5,
    #             safety_order_step_scale=1.56,
    #             safety_order_price_deviation_percent=1.3,
    #             base_order_size_usd=20,
    #             safety_order_size_usd=3
    #             # total_usd=self.broker.get_cash()
    #         )
    # dca.print_table()
    # sys.exit()

    btc()



