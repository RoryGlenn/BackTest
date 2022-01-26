# https://www.youtube.com/watch?v=5VU3CJMuk0w

# To get free crypto data
# https://www.CryptoDataDownload.com


# Backtrader documentation on custom CSV files
# https://www.backtrader.com/docu/datafeed/

from strategies.DCA3C.dca3c_strategy import DCA3C
from strategies.DCA3C.dca3c_strategy import DCA
from strategies.DCA3C.dca_dynamic    import DCADynamic

from strategies.DCA3C.buy_and_hold   import BuyAndHold
from observers.stop_take             import SLTPTracking

import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time

STARTING_CASH = 1000000
BTC_USD_2017  = "historical_data/BTCUSD/Bitstamp_BTCUSD_2017_minute.csv"
BTC_USD_2018  = "historical_data/BTCUSD/Bitstamp_BTCUSD_2018_minute.csv"
ORACLE        = "historical_data/oracle.csv"
BNGO          = "historical_data/BNGO.csv"



"""
TODO
    1. Create an optimizer for the DCA settings.
        Optimizer will iterate through a large list of settings.
        Will try different combinations for.

    2. Implement trailing percent       DONE

    2. Create a dynamic or static DCA: 
        a. dynamic DCA will be a percentage given for the base order and the safety order.
        b. use_all_cash boolean: Will use all available money on the placement of the final safety order in order to maximize profit.
        
        CHECK THIS WORKS BY ENTERING IN THE BASE ORDER PRICE AND SAFETY ORDER PRICE WITH THE REGULUAR DCA.
        DOUBLE CHECK BOTH OF THESE BY ENTERING IT INTO 3COMMAS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    3. PULL DATA FROM CRYPTO FUTURES TO SEE WHEN LIQUIDATION OCCURES
    4. Time frames: Buy and hold might win out in the long run, but what time frames does DCA when out?

"""

def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"


def oracle() -> None:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(ORACLE)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    # ORACLE
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(1995, 1, 3),
                               todate=datetime.datetime(2014, 12, 31))

    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)
    # cerebro.addstrategy(BuyAndHold)
    cerebro.addobserver(SLTPTracking)

    cerebro.run()
    cerebro.plot(style='candlestick', numfigs=1,
                    barup='green', bardown='red',
                    barupfill=True, bardownfill=True,
                    volup='green', voldown='red', voltrans=100.0, voloverlay=False)
    return


def bngo() -> None:
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df         = pd.read_csv(BNGO)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    # BNGO
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(2018, 8, 21),
                               todate=datetime.datetime(2022, 1, 20))
    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)
    # cerebro.addstrategy(BuyAndHold)
    cerebro.addobserver(SLTPTracking)

    cerebro.run()
    cerebro.plot(style='candlestick', numfigs=1,
                    barup='green', bardown='red',
                    barupfill=False, bardownfill=False,
                    volup='green', voldown='red', voltrans=10.0, voloverlay=False)

    return


def btc_2018() -> None:
    testtime = time.time()
    
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(BTC_USD_2018, 
                     low_memory=False, 
                     usecols=['unix', 'date', 'symbol', 'open', 'high', 'low', 'close', 'Volume USD'])
    df = df[::-1] # reverse the data

    df.drop("unix", axis=1, inplace=True)
    df.rename(columns={"Volume USD": 'Volume'})

    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df.set_index('date', inplace=True)

    # BTC 2018
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(2018, 1, 1),
                               todate=datetime.datetime(2018, 12, 31))
    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)
    # cerebro.addstrategy(BuyAndHold)
    # cerebro.addobserver(SLTPTracking)

    cerebro.run()

    print(f"Test time elapsed (is this number different?): {get_elapsed_time(testtime)}")

    cerebro.plot(style='candlestick', numfigs=1,
                    barup='green', bardown='red',
                    barupfill=False, bardownfill=False,
                    volup='green', voldown='red', voltrans=10.0, voloverlay=False)
    return



if __name__ == '__main__':
    os.system("cls")

    # oracle()
    # bngo()
    btc_2018()