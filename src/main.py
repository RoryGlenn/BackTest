# https://www.youtube.com/watch?v=5VU3CJMuk0w

# To get free crypto data
# https://www.CryptoDataDownload.com


# Backtrader documentation on custom CSV files
# https://www.backtrader.com/docu/datafeed/

from strategies.DCA3C.dca3c_strategy import DCA3C
from strategies.DCA3C.dca3c_strategy import DCA

import backtrader as bt
import pandas     as pd

import datetime
import os


STARTING_CASH = 1000000
BTC_USD       = "historical_data/BTCUSD/Bitstamp_BTCUSD_2017_minute.csv"
ORACLE        = "historical_data/oracle.csv"
BNGO          = "historical_data/BNGO.csv"


"""
TODO
    1. Create an optimizer for the DCA settings.
        Optimizer will iterate through a large list of settings. 
        Will try different combinations for 

    2. implement trailing percent

    2. Create a dynamic or static DCA: 
        a. dynamic DCA will be a percentage given for the base order and the safety order.
        b. use_all_cash boolean: Will use all available money on the placement of the final safety order in order to maximize profit.

    3. PULL DATA FROM CRYPTO FUTURES TO SEE WHEN LIQUIDATION OCCURES
    4. Time frames: Buy and hold might win out in the long run, but what time frames does DCA when out?

"""


if __name__ == '__main__':
    os.system("cls")

    dca = DCA(1, 1, 7, 7, 2.5, 1.56, 1.3, 1, 0.5)
    dca.print_df_table()
    
    
    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df         = pd.read_csv(BNGO)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    
    df.set_index('Date', inplace=True)
    
    data = bt.feeds.PandasData(dataname=df,
                               fromdate=datetime.datetime(2018, 8, 21),
                               todate=datetime.datetime(2022, 1, 20))
    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)

    cerebro.run()
    cerebro.plot()


"""
BNGO
^^^^ Finished Backtesting ^^^^^
Total time tested:     1248 days, 0:00:00
Total Profit:          $1,696,571.520000
ROI:                   169.66%
Final Portfolio Value: $2,696,571.520000

"""