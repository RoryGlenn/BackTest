from __future__ import (absolute_import, division, print_function, unicode_literals)
from dca        import DCA
from backtrader_plotting         import Bokeh
from backtrader_plotting.schemes import Blackly


import backtrader as bt
import pandas     as pd

import datetime
import os
import sys
import time


TEN_THOUSAND          = 10000
BTC_USD_1DAY_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN     = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"

BTCUSD_DECIMAL_PLACES = 5

p              = None
period_results = dict()


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"



class DCA3C(bt.Strategy):
    # SCALP 15
    params = (
        ('target_profit_percent',        1),
        ('trail_percent',                0.002), # even though it says its a percent, its a decimal -> 0.2%
        ('safety_orders_max',            15),
        ('safety_orders_active_max',     15),
        ('safety_order_volume_scale',    1.2),
        ('safety_order_step_scale',      1.16),
        ('safety_order_price_deviation', 1.0),
        ('base_order_size_usd',          20),
        ('safety_order_size_usd',        10)
    )

    ############################################################################################

    def __init__(self) -> None:
        self.count = 0

        # Store all the Safety Orders so we can cancel the unfilled ones after TPing
        self.safety_orders = []

        # Store the take profit order so we can cancel and update take profit price with every filled safety order
        self.take_profit_order = None
        
        self.dca                   = None
        self.time_period           = None
        self.is_first_safety_order = True

        self.start_cash            = 0
        self.start_value           = 0
        return

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt      = dt or self.data.datetime[0]
        # minutes = self.datas[0].datetime.time(0)

        if isinstance(dt, float):
            dt = bt.num2date(dt)

        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def money_format(self, money: float) -> str:
        return "${:,.6f}".format(money)

    def print_ohlc(self) -> None:
        date    = self.data.datetime.date()
        minutes = self.datas[0].datetime.time(0)
        open    = self.money_format(self.data.open[0])
        high    = self.money_format(self.data.high[0])
        low     = self.money_format(self.data.low[0])
        close   = self.money_format(self.data.close[0])
        print(f"[{date} {minutes}] Open: {open}, High: {high}, Low: {low}, Close: {close}\r", end='')
        return

    def __set_take_profit(self) -> None:
        if self.take_profit_order is None:
            return

        # print("\nCANCELED TAKE PROFIT SELL ORDER")
        # print(f"Price: {self.money_format(self.take_profit_order.price)}, Size: {self.take_profit_order.size}\n")

        safety_order = None

        if self.is_first_safety_order:
            self.is_first_safety_order = False

            self.take_profit_order = self.sell(price=self.dca.required_price_levels[0],
                                               size=self.dca.total_quantity_levels[0],
                                               trailpercent=self.params.trail_percent,
                                               plimit=self.dca.required_price_levels[0],
                                               exectype=bt.Order.StopTrailLimit)
            
            self.dca.remove_top_safety_order()

            safety_order = self.buy(price=self.dca.price_levels[0],
                                    size=self.dca.safety_order_quantity_levels[0],
                                    exectype=bt.Order.Limit,
                                    oco=self.take_profit_order) # oco = One Cancel Others
        else:
            self.take_profit_order = self.sell(price=self.dca.required_price_levels[0],
                                               size=self.dca.total_quantity_levels[0],
                                               trailpercent=self.params.trail_percent,
                                               plimit=self.dca.required_price_levels[0],
                                               exectype=bt.Order.StopTrailLimit)

            self.dca.remove_top_safety_order()

            # check if we have placed all safety orders
            if len(self.dca.price_levels) > 0:
                safety_order = self.buy(price=self.dca.price_levels[0],
                                        size=self.dca.safety_order_quantity_levels[0],
                                        exectype=bt.Order.Limit,
                                        oco=self.take_profit_order) # oco = One Cancel Others

        self.safety_orders.append(safety_order)
        
        # print("\nNEW TAKE PROFIT ORDER")
        # print(f"Price: {self.money_format(self.take_profit_order.price)}, Size: {self.take_profit_order.size}")
        # print()
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: {:,.8f} Price: {:,.8f}, Cost: {:,.8f}, Comm {:,.8f}'.format(order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                if order.exectype == 0:
                    entry_price       = order.executed.price
                    base_order_size   = order.executed.size
                    size              = self.params.safety_order_size_usd

                    # If the cost of the stock/coin is larger than our base order size, 
                    # then we can't order in integer sizes. We must order in fractional sizes                    
                    safety_order_size = size//entry_price if size//entry_price != 0 else size/entry_price

                    self.dca = DCA( entry_price_usd=entry_price,
                                    target_profit_percent=self.params.target_profit_percent,
                                    safety_orders_max=self.params.safety_orders_max,
                                    safety_orders_active_max=self.params.safety_orders_active_max,
                                    safety_order_volume_scale=self.params.safety_order_volume_scale,
                                    safety_order_step_scale=self.params.safety_order_step_scale,
                                    safety_order_price_deviation_percent=self.params.safety_order_price_deviation,
                                    base_order_size=base_order_size,
                                    safety_order_size=safety_order_size,
                                    total_usd=self.broker.get_cash()
                                )
                    
                    take_profit_price = self.dca.base_order_required_price

                    # BASE ORDER SELL (TAKE PROFIT: if this sell is filled, cancel all the other safety orders)
                    self.take_profit_order = self.sell(price=take_profit_price,
                                                        size=base_order_size,
                                                        trailpercent=self.params.trail_percent,
                                                        plimit=take_profit_price,
                                                        exectype=bt.Order.StopTrailLimit)

                    """instead of submitting the takeprofit and all safety orders at a single time,
                    submit one safety order and one take profit order until one of them is canceled!"""
                    safety_order = self.buy(price=self.dca.price_levels[0],
                                                size=self.dca.safety_order_quantity_levels[0],
                                                exectype=bt.Order.Limit,
                                                oco=self.take_profit_order) # oco = One Cancel Others

                    self.safety_orders.append(safety_order)
            elif order.issell():
                self.log('SELL EXECUTED, Size: {:,.8f} Price: {:,.8f}, Cost: {:,.8f}, Comm {:,.8f}'.format(order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                
                if self.position.size != 0:
                    print()
                    print(self.position)
                    print()

                # reset variables
                self.safety_orders         = []
                self.take_profit_order     = None
                self.is_first_safety_order = True
        elif order.status in [order.Canceled]:
            # if the sell was canceled, that means a safety order was filled and its time to put in a new updated take profit order.
            if order.issell():
                self.__set_take_profit()
            elif order.isbuy():
                self.log(f'BUY ORDER CANCELED: Size: {order.size}')
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            print()
            print("Cash:", self.broker.get_cash())
            print("Value", self.broker.get_value())
            print()
            print(order)
            print()
            self.dca.print_table()
            print()
            sys.exit()
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.size, order.price, order.value, order.comm))
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
            self.log('OPERATION PROFIT, GROSS %.6f, NET %.6f, Size: %.6f' % (trade.pnl, trade.pnlcomm, trade.size))

            if trade.pnl <= 0 or trade.pnlcomm <= 0:
                print(trade.pnl, trade.pnlcomm)
                print()
                print(trade)
                print()
        return

    def __start_new_deal(self) -> None:
        # print("\n*** NEW DEAL ***")

        # BASE ORDER BUY
        entry_price = self.data.close[0]
        size        = self.params.base_order_size_usd // entry_price

        # If the cost of the stock/coin is larger than our base order size, 
        # then we can't order in integer sizes. We must order in fractional sizes
        base_order_size = size if size != 0 else self.params.base_order_size_usd/entry_price
        
        buy_order = self.buy(size=base_order_size, exectype=bt.Order.Market)
        self.safety_orders.append(buy_order)
        return

    def prenext(self) -> None:
        print(f"Prenext count: {self.count}\r", end='') 
        self.count += 1
        return

    def next(self) -> None:
        self.print_ohlc()

        if len(self.safety_orders) == 0:
            self.__start_new_deal()
        return

    def start(self) -> None:
        self.time_period = self.datas[0].p.todate - self.datas[0].p.fromdate
        self.start_cash  = self.broker.get_cash()
        self.start_value = self.broker.get_value()
        return

    def stop(self) -> None:
        global period_results

        total_value = self.broker.get_value()
        profit      = total_value - self.start_cash
        roi         = ((total_value / self.start_cash) - 1.0) * 100
        roi         = '{:.2f}%'.format(roi)

        profit           = self.money_format(round(profit, 2))
        self.start_value = self.money_format(round(self.start_value, 2))
        total_value      = self.money_format(round(total_value, 2))

        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print("##########################################")

        print(f"*** Period {p} results ***")

        print('target_profit_percent:         ', self.params.target_profit_percent)
        print('trail_percent:                 ', self.params.trail_percent)
        print('safety_orders_max:             ', self.params.safety_orders_max)
        print('safety_orders_active_max:      ', self.params.safety_orders_max)
        print('safety_order_volume_scale:     ', self.params.safety_order_volume_scale)
        print('safety_order_step_scale:       ', self.params.safety_order_step_scale)
        print('safety_order_price_deviation:  ', self.params.safety_order_price_deviation)
        print('base_order_size_usd:           ', self.params.base_order_size_usd)

        print()
        print(f"Time period:           {self.time_period}")
        print(f"Total Profit:          {profit}")
        print(f"ROI:                   {roi}")
        print(f"Start Portfolio Value: {self.start_value}")
        print(f"Final Portfolio Value: {total_value}")
        print("##########################################")
        
        period_results[p] = roi
        return


def get_period(period: int) -> datetime:
    start_date = None
    end_date   = None

    if period == 0:
        # a short time frame to run a quick test only
        start_date = datetime.datetime(year=2021, month=7, day=1, hour=0, minute=0)
        end_date   = datetime.datetime(year=2021, month=7, day=7, hour=0, minute=0) 
        return start_date, end_date

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
        start_date = datetime.datetime(year=2019, month=7,  day=1,  hour=0, minute=1)
        end_date   = datetime.datetime(year=2019, month=11, day=19, hour=0, minute=1)
    elif period == 4:
        # period 4: (7/1/2017 - 11/19/2017)
        start_date = datetime.datetime(year=2017, month=7,  day=1,  hour=0, minute=1)
        end_date   = datetime.datetime(year=2017, month=11, day=19, hour=0, minute=1)        
    elif period == 5:
        # period 5: (1/28/21 - 4/15/21)
        start_date = datetime.datetime(year=2021, month=1, day=28, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=4, day=15, hour=0, minute=1)
    elif period == 6:
        # period 6: (7/20/2021 -> 9/5/2021)
        start_date = datetime.datetime(year=2021, month=7, day=20, hour=0, minute=1)
        end_date   = datetime.datetime(year=2021, month=9, day=5,  hour=0, minute=1)
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

    for period in range(0, 1): # PERIOD 1-10
        start_date, end_date = get_period(period)

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
        
        cerebro.addstrategy(DCA3C)

        p = period

        print()
        print("^^^^ STARTING THE BACKTEST ^^^^^")
        print(f"*** Testing period {p} ***")
        print()

        cerebro.run()

        b = Bokeh(style='bar', filename='backtest_results/Scalp.html', output_mode='show', scheme=Blackly())
        cerebro.plot(b)

    for period, roi in period_results.items():
        print(f"period: {period}, roi: {roi}")




"""

        SCALP 7

            period 1: 4/14/2021 - 7/21/2021   roi: 2.01%
            period 2: 1/7/2018  - 4/1/2018    roi: 2.50%
            period 3: 7/1/2019  - 11/19/2019  roi: 1.09%
            
            period 4: 7/1/2017  - 11/19/2017  roi: 2.37%
            period 5: 1/28/2021 - 4/15/2021   roi: 1.40%
            period 6: 7/20/2021 - 9/5/2021    roi: 0.43%
            
            period 7: 5/9/2021  - 9/9/2021    roi: 2.04%
            period 8: 1/1/2019  - 5/5/2019    roi: 0.48%
            period 9: 1/1/2019  - 4/1/2019    roi: 0.23%
            
            period 10: 1/1/2016 - 1/1/2022    roi: 39.47%


    ##############################################

        SCALP 15
            period 1: 4/14/2021 - 7/21/2021     6.83%
            period 2: 1/7/2018  - 4/1/2018     4.08%
            period 3: 7/1/2019  - 11/19/2019   3.12%

            period 4: 7/1/2017  - 11/19/2017   9.22%
            period 5: 1/28/2021 - 4/15/2021    5.78%
            period 6: 7/20/2021 - 9/5/2021     1.84%

            period 7: 5/9/2021  - 9/9/2021     8.91%
            period 8: 1/1/2019  - 5/5/2019     1.64%
            period 9: 1/1/2019  - 4/1/2019     0.81%

            period 10: 1/1/2016 - 1/1/2022      174.55%

"""