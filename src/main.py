# https://www.youtube.com/watch?v=5VU3CJMuk0w

# To get free crypto data
# https://www.CryptoDataDownload.com


# Backtrader documentation on custom CSV files
# https://www.backtrader.com/docu/datafeed/


import backtrader
import datetime
import time
import os

from strategies.DCA.my_dca_strategy   import DCAStrategy
from order_observer import OrderObserver

STARTING_CASH = 1000000
BTC_USD       = "historical_data/BTCUSD/Bitstamp_BTCUSD_2017_minute.csv"
ORACLE        = "historical_data/oracle.csv"


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"



if __name__ == '__main__':
    os.system("cls")

    start_time = time.time()
    cerebro    = backtrader.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    #BTC-USD
    data = backtrader.feeds.YahooFinanceCSVData(dataname=ORACLE,
                                                fromdate=datetime.datetime(1995, 1, 3),
                                                todate=datetime.datetime(2014, 12, 31),
                                                adjclose=False)


    # DO NOT DELETE THIS!!!!!!!!!!!!!!!!!!!!!!!!
    # This WORKS!!!!!!!!!!!
    # data = backtrader.feeds.GenericCSVData(dataname=BTC_USD,
    #                                        dtformat="%Y-%m-%d %H:%M:%S",
    #                                        fromdate=datetime.datetime(2017, 1, 1, 0, 1, 0),
    #                                        todate=datetime.datetime(2017, 12, 31, 23, 59, 0),

    #                                        nullvalue=0.0,

    #                                        time=-1,
    #                                        datetime=0,
    #                                        open=1,
    #                                        high=2,
    #                                        low=3,
    #                                        close=4,
    #                                        volume=5,

    #                                        openinterest=-1
    #                                     )


    cerebro.adddata(data)
    # cerebro.addobserver(OrderObserver)
    cerebro.addstrategy(DCAStrategy)

    starting_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: {starting_value}")
    cerebro.run()

    print()
    profit = round(cerebro.broker.getvalue() - starting_value, 2)
    print(f"Final Portfolio Value: ${round(cerebro.broker.getvalue(), 2)}")
    print(f"Total Profit: ${profit}")
    print(f"Total time taken: {get_elapsed_time(start_time)}")
    cerebro.plot()