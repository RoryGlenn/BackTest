from dca import DCA
from dca3c_strategy import DCA3C


from backtrader_plotting             import Bokeh  
from backtrader_plotting.schemes     import Blackly

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time


ONE_MILLION  = 1000000
TEN_THOUSAND = 10000
ONE_THOUSAND = 1000

ORACLE       = "historical_data/stocks/oracle.csv"
BNGO         = "historical_data/stocks/BNGO.csv"
FILE         = ""

BTC_USD_1DAY_ALL  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2017_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2017_1min.csv"
BTC_USD_2018_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2018_1min.csv"
BTC_USD_2019_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2019_1min.csv"
BTC_USD_2020_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2020_1min.csv"
BTC_USD_2021_1MIN = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_ALL_1MIN  = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"



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
        periods 1-3: bear markets
        periods 4-6: bull markets
        periods 7-9: sideways/neutral markets

    """

    """
        To incorporate MA_200_Day, HullMA_20_Day for bull markets and DCA for bear markets,
        we need to figure out how to calculate a MA_200_Day while simultaneously calculating the HullMA_20_Day.

        2 different indicators using 2 different number of days.
    
    
    """

    #############################################################################
    # period 1 ALT: (4/14/2021 - 7/21/21)
    FILE1       = BTC_USD_2021_1MIN
    start_date = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1)
    end_date   = datetime.datetime(year=2021, month=2, day=1, hour=0, minute=1)

    # Day values
    FILE2       = BTC_USD_1DAY_ALL
    start_date = datetime.datetime(year=2015, month=10, day=8)
    end_date   = datetime.datetime(year=2022, month=1, day=28)
    #############################################################################


    # period 1: (4/14/2021 - 7/21/21)
    # FILE1       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=4, day=14, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=7, day=21, hour=0, minute=1)

    # period 2: (1/7/2018 - 4/1/2018)
    # FILE1       = BTC_USD_2018
    # start_date = datetime.datetime(year=2018, month=1, day=7, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2018, month=4, day=1, hour=0, minute=1)

    # period 3: (7/1/2019 - 11/19/2019)
    # FILE1       = BTC_USD_2019
    # start_date = datetime.datetime(year=2019, month=7, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2019, month=11, day=19, hour=0, minute=1)

    # period 4: (7/1/2017 - 11/19/2017)
    # FILE1       = BTC_USD_2017
    # start_date = datetime.datetime(year=2017, month=9, day=20, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2017, month=12, day=17, hour=0, minute=1)

    # period 5: (1/28/21 - 4/15/21)
    # FILE1       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=1, day=28, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=4, day=15, hour=0, minute=1)

    # period 6: (7/20/2021 -> 9/5/2021)
    # FILE1       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=7, day=20, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=9, day=5, hour=0, minute=1)

    # period 7: 5/9/21 -> 9/9/21
    # FILE1       = BTC_USD_2020
    # start_date = datetime.datetime(year=2020, month=5, day=9, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2020, month=9, day=9, hour=0, minute=1)

    # period 8: 5/9/21 -> 9/9/21
    # FILE1       = BTC_USD_2019
    # start_date = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2019, month=5, day=1, hour=0, minute=1)

    # period 9: 1/1/2019 -> 4/1/19
    # FILE1       = BTC_USD_2019
    # start_date = datetime.datetime(year=2019, month=1, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2019, month=4, day=1, hour=0, minute=1)

    # period 10: 1/1/2016 -> 1/26/2022
    # FILE1       = BTC_USD_ALL
    # start_date = datetime.datetime(year=2016, month=1, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2022, month=1, day=1, hour=0, minute=1)
    
    # small testing dates only
    # FILE       = BTC_USD_2021
    # start_date = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1)
    # end_date   = datetime.datetime(year=2021, month=2, day=1, hour=0, minute=1)
    ##############################################################################

    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str   = end_date.strftime(  "%Y-%m-%d %H:%M:%S")

    df = pd.read_csv(FILE1,
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

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data, name='BTCUSD') # adding a name while using bokeh will avoid plotting error
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Days)
    cerebro.addstrategy(DCA3C)

    # adding observers
    cerebro.addobserver(bt.observers.DrawDown)

    # adding indicators
    # cerebro.addindicator(bt.indicators.HullMovingAverage, period=28800, plotname="HullMA_20_Day") # 28,800 Minutes = 20 Days

    # adding analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.VWR,         timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.PeriodStats, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.SQN)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    
    # cerebro.run(runonce=False)
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    # b = Bokeh(style='bar', filename='backtest_results/testgraph.html', output_mode='show', scheme=Blackly())
    # cerebro.plot(b)
    cerebro.plot() # if the current test fails, run it like this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return




def btc_bear_bull() -> None:
    start_time = time.time()

    #############################################################################
    # period 1 ALT: (4/14/2021 - 7/21/21)
    FILE1       = BTC_USD_2021_1MIN
    start_date1 = datetime.datetime(year=2021, month=1, day=1, hour=0, minute=1)
    end_date1   = datetime.datetime(year=2021, month=4, day=1, hour=0, minute=1)

    # Day values
    FILE2       = BTC_USD_1DAY_ALL
    start_date2 = datetime.datetime(year=2015, month=10, day=8)
    end_date2   = datetime.datetime(year=2022, month=1, day=28)
    #############################################################################

    df_minute = pd.read_csv(FILE1,
                     low_memory=False,
                     usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'],
                     parse_dates=True,
                     skiprows=1)
    
    df_day = pd.read_csv(FILE2,
                     low_memory=False,
                     usecols=['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume'],
                     parse_dates=True,
                     skiprows=1)

    # reverse the data
    df_minute = df_minute[::-1]
    df_day    = df_day[::-1]

    df_minute['Date'] = pd.to_datetime(df_minute['Date']).dt.tz_localize(None)
    df_minute.set_index('Date', inplace=True)

    df_day['Date'] = pd.to_datetime(df_day['Date']).dt.tz_localize(None)
    df_day.set_index('Date', inplace=True)

    # BTC/USD
    data_minute = bt.feeds.PandasData(dataname=df_minute, 
                                        timeframe=bt.TimeFrame.Minutes,
                                        fromdate=start_date1,
                                        todate=end_date1)

    data_day = bt.feeds.PandasData(dataname=df_day, 
                                    timeframe=bt.TimeFrame.Days,
                                    fromdate=start_date2,
                                    todate=end_date2)

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(TEN_THOUSAND)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% of the operation value

    cerebro.adddata(data_minute, name='BTCUSD_MINUTE') # adding a name while using bokeh will avoid plotting error
    cerebro.adddata(data_day, name='BTCUSD_DAY') # adding a name while using bokeh will avoid plotting error
    # cerebro.resampledata(data_minute, timeframe=bt.TimeFrame.Days)
    cerebro.addstrategy(DCA3C)

    # adding observers
    cerebro.addobserver(bt.observers.DrawDown)

    # adding indicators
    # cerebro.addindicator(bt.indicators.HullMovingAverage, period=28800, plotname="HullMA_20_Day") # 28,800 Minutes = 20 Days

    # adding analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.VWR,         timeframe=bt.TimeFrame.Months)
    cerebro.addanalyzer(bt.analyzers.PeriodStats, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.SQN)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)

    print("\n^^^^ STARTING THE BACKTEST ^^^^^")
    
    # cerebro.run(runonce=False)
    cerebro.run()

    print(f"Time elapsed: {get_elapsed_time(start_time)}")

    b = Bokeh(style='bar', filename='backtest_results/testgraph.html', output_mode='show', scheme=Blackly())
    cerebro.plot(b)
    # cerebro.plot() # if the current test fails, run it like this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    return


if __name__ == '__main__':
    os.system("cls")
    # btc_bear_bull()


    dca = DCA( entry_price_usd=50000,
                    target_profit_percent=1,
                    safety_orders_max=7,
                    safety_orders_active_max=7,
                    safety_order_volume_scale=2.5,
                    safety_order_step_scale=1.56,
                    safety_order_price_deviation_percent=1.3,
                    base_order_size_usd=10,
                    safety_order_size_usd=10
                )

    dca.print_table()
