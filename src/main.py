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
import sys

from strategies.DCA3C.dca_dynamic import DCADynamic


STARTING_CASH = 1000000
BTC_USD       = "historical_data/BTCUSD/Bitstamp_BTCUSD_2017_minute.csv"
ORACLE        = "historical_data/oracle.csv"
BNGO          = "historical_data/BNGO.csv"


"""
TODO
    1. Create an optimizer for the DCA settings.
        Optimizer will iterate through a large list of settings.
        Will try different combinations for.

    2. Implement trailing percent

    2. Create a dynamic or static DCA: 
        a. dynamic DCA will be a percentage given for the base order and the safety order.
        b. use_all_cash boolean: Will use all available money on the placement of the final safety order in order to maximize profit.
        
        CHECK THIS WORKS BY ENTERING IN THE BASE ORDER PRICE AND SAFETY ORDER PRICE WITH THE REGULUAR DCA.
        DOUBLE CHECK BOTH OF THESE BY ENTERING IT INTO 3COMMAS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    3. PULL DATA FROM CRYPTO FUTURES TO SEE WHEN LIQUIDATION OCCURES
    4. Time frames: Buy and hold might win out in the long run, but what time frames does DCA when out?

"""


if __name__ == '__main__':
    os.system("cls")

    STARTING_CASH     = 1000
    base_order_size   = STARTING_CASH*0.0081
    safety_order_size = base_order_size/2

    # ADA
    # dca = DCA(entry_price=1.076,
    #           target_profit_percent=1,
    #           safety_orders_max=7,
    #           safety_orders_active_max=7,
    #           safety_order_volume_scale=2.5,
    #           safety_order_step_scale=1.56,
    #           safety_order_price_deviation=1.3,
    #           base_order_size=1,
    #           safety_order_size=1)

    dca = DCA(entry_price_usd=2364.33,
              target_profit_percent=1,
              safety_orders_max=7,
              safety_orders_active_max=7,
              safety_order_volume_scale=2.5,
              safety_order_step_scale=1.56,
              safety_order_price_deviation_percent=1.3,
            #   base_order_size_usd=10,
            #   safety_order_size_usd=10
              base_order_size=1,
              safety_order_size=1
              )

    dca.print_table()


    # dca = DCADynamic(1, 1, 7, 7, 2.5, 1.56, 1.3, STARTING_CASH)
    # print(dca.deviation_percent_levels)
    # print(dca.price_levels)
    sys.exit()
    
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