from strategies.DCA3C.dca3c_strategy import DCA
from strategies.DCA3C.dca3c_strategy import DCA3C
from strategies.DCA3C.dca_dynamic    import DCADynamic

from strategies.buy_and_hold         import BuyAndHold
from observers.stop_take             import SLTPTracking

from backtrader_plotting             import Bokeh, OptBrowser
from backtrader_plotting.schemes     import Blackly, Tradimo

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time


ONE_MILLION  = 1000000
ONE_THOUSAND = 1000

BTC_USD_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"
BTC_USD_2017 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2017_1min.csv"
BTC_USD_2018 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2018_1min.csv"
BTC_USD_2021 = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
ORACLE       = "historical_data/stocks/oracle.csv"
BNGO         = "historical_data/stocks/BNGO.csv"


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

    """
    3 bad periods
    3 neutral periods
    3 good periods
    """

    # # just for testing optimization
    # start_date = datetime.datetime(year=2018, month=1, day=7, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2018, month=1, day=8, hour=0, minute=1)

    # period 1: (4/14/2021 - 7/21/21)
    start_date = datetime.datetime(year=2021, month=4, day=14, hour=0, minute=1)
    end_date   = datetime.datetime(year=2021, month=7, day=21, hour=0, minute=1)

    # period 2: (1/7/2018 - 4/1/2018)
    # start_date = datetime.datetime(year=2018, month=1, day=7, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2018, month=4, day=1, hour=0, minute=1)


    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str   = end_date.strftime("%Y-%m-%d %H:%M:%S")

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
    data = bt.feeds.PandasData(
                                dataname=df,
                                timeframe=bt.TimeFrame.Minutes,

                                # 2015
                                # fromdate=datetime.datetime(year=2015, month=10, day=8, hour=13, minute=40),
                                # todate=datetime.datetime(year=2015, month=12, day=31, hour=23, minute=59)

                                # 2016
                                # fromdate=datetime.datetime(year=2016, month=1, day=1, hour=0, minute=1),
                                # todate=datetime.datetime(year=2016, month=12, day=31, hour=23, minute=59)

                                # 2017
                                # fromdate=datetime.datetime(year=2017, month=1, day=1, hour=0, minute=1),
                                # todate=datetime.datetime(year=2017, month=12, day=31, hour=23, minute=59)

                                # 2018
                                # fromdate=datetime.datetime(year=2018, month=1,  day=1,  hour=0,  minute=1),
                                # todate=datetime.datetime(year=2018, month=12, day=31, hour=23, minute=59)

                                # 2019
                                # fromdate=datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1),
                                # todate=datetime.datetime(year=2019, month=12, day=31, hour=23, minute=59)

                                # 2020
                                # fromdate=datetime.datetime(year=2020, month=1, day=1, hour=0, minute=1),
                                # todate=datetime.datetime(year=2020, month=12, day=31, hour=23, minute=59)

                                # 2021
                                # fromdate=datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1),
                                # todate=datetime.datetime(year=2021, month=12, day=31, hour=23, minute=59)

                                # ALL!!!
                                # fromdate=datetime.datetime(year=2015, month=10, day=8, hour=13, minute=41),
                                # todate=datetime.datetime(year=2022, month=1, day=26, hour=0, minute=4)

                                # Extra testing...
                                fromdate=start_date,
                                todate=end_date
                            )

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(ONE_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data, name='BTC/USD-ALL') # adding a name while using bokeh will avoid plotting error
    cerebro.addstrategy(DCA3C)
    # cerebro.addstrategy(BuyAndHold)

    # adding analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.VWR,         timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.PeriodStats, timeframe=bt.TimeFrame.Days)
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
    #             safety_orders_max=15,
    #             safety_orders_active_max=15,
    #             safety_order_volume_scale=1.2,
    #             safety_order_step_scale=1.16,
    #             safety_order_price_deviation_percent=1,
    #             base_order_size_usd=26,
    #             safety_order_size_usd=13
    #             # total_usd=self.broker.get_cash()
    #         )
    # dca.print_table()

    # sys.exit()

    btc()




"""
NOT OPTIMIZED
Time period:           98 days, 0:00:00
Total Profit:          $60.840000
ROI:                   6.08%
Start Portfolio Value: $1,000.000000
Final Portfolio Value: $1,060.840000
Time elapsed: 2 minutes 45 seconds



###########################################################
OPTIMIZED
Time period:           98 days, 0:00:00
Total Profit:          $69.900000
ROI:                   6.99%
Start Portfolio Value: $1,000.000000
Final Portfolio Value: $1,069.900000
Time elapsed: 2 minutes 56 seconds

"""