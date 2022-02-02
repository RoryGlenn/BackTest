from __future__                  import (absolute_import, division, print_function, unicode_literals)
from dca                         import DCA
from backtrader_plotting         import Bokeh  
from backtrader_plotting.schemes import Blackly

import backtrader as bt
import pandas     as pd

import datetime
import os
import math
import sys

from strategies.BHDCA.dca3c import DCA3C


TEN_THOUSAND          = 10000
BTC_USD_1DAY_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_day.csv"
BTC_USD_2021_1MIN     = "historical_data/gemini/BTCUSD/gemini_BTCUSD_2021_1min.csv"
BTC_USD_1MIN_ALL      = "historical_data/gemini/BTCUSD/gemini_BTCUSD_1min_all.csv"

BTCUSD_DECIMAL_PLACES = 5

p              = None
period_results = dict()


class BHDCA(bt.Strategy):
    params = (
        # bh params
        ('bh_target_profit_percent', 2),
        # ('bh_trail_percent',         0.01), # 1%

        # dca params
        ('dca_target_profit_percent',        1),
        ('dca_trail_percent',                0.002), # 0.2%
        ('dca_safety_orders_max',            15),
        ('dca_safety_orders_active_max',     15),
        ('dca_safety_order_volume_scale',    1.2),
        ('dca_safety_order_step_scale',      1.16),
        ('dca_safety_order_price_deviation', 1.0),
        ('dca_base_order_size_usd',          250),
        ('dca_safety_order_size_usd',        250)
    )
    ############################################################################################

    def __init__(self) -> None:
        # day values
        self.hullma = bt.indicators.HullMovingAverage(self.datas[1],   period=20)
        self.sma    = bt.indicators.MovingAverageSimple(self.datas[1], period=200)

        # Store all the Safety Orders so we can cancel the unfilled ones
        self.safety_orders          = []
        self.safety_order_sizes_usd = []

        # Store the take profit order so we can cancel and update take profit price with every filled safety order
        self.dca                   = None
        self.time_period           = None
        self.bh_take_profit_order  = None
        self.dca_take_profit_order = None
        
        self.is_first_safety_order = True
        self.is_dca                = False
        
        self.start_cash            = 0
        self.start_value           = 0
        self.prenext_count         = 1
        return

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]

        if isinstance(dt, float):
            dt = bt.num2date(dt)

        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def round_decimals_down(self, number: float, decimals: int=2) -> int | float:
        """Returns a value rounded down to a specific number of decimal places."""
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)
        factor = 10 ** decimals
        return math.floor(number * factor) / factor

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

    def __dca_set_take_profit(self) -> None:
        if self.dca_take_profit_order is None:
            return




        safety_order = None

        if self.is_first_safety_order:
            self.is_first_safety_order = False

            self.dca_take_profit_order = self.sell(price=self.dca.required_price_levels[0],
                                               size=self.dca.total_quantity_levels[0],
                                               trailpercent=self.params.dca_trail_percent,
                                               plimit=self.dca.required_price_levels[0],
                                               exectype=bt.Order.StopTrailLimit)
            
            self.dca.remove_top_safety_order()

            safety_order = self.buy(price=self.dca.price_levels[0],
                                    size=self.dca.safety_order_quantity_levels[0],
                                    exectype=bt.Order.Limit,
                                    oco=self.dca_take_profit_order) # oco = One Cancel Others
        else:
            self.dca_take_profit_order = self.sell(price=self.dca.required_price_levels[0],
                                               size=self.dca.total_quantity_levels[0],
                                               trailpercent=self.params.dca_trail_percent,
                                               plimit=self.dca.required_price_levels[0],
                                               exectype=bt.Order.StopTrailLimit)

            self.dca.remove_top_safety_order()

            # check if we have placed all safety orders
            if len(self.dca.price_levels) > 0:
                safety_order = self.buy(price=self.dca.price_levels[0],
                                        size=self.dca.safety_order_quantity_levels[0],
                                        exectype=bt.Order.Limit,
                                        oco=self.dca_take_profit_order) # oco = One Cancel Others

        self.safety_orders.append(safety_order)
        



        return

    def __dca_start_new_deal(self) -> None:
        # BASE ORDER BUY
        entry_price = self.data.close[0]
        size        = self.params.dca_base_order_size_usd // entry_price

        # If the cost of the stock/coin is larger than our base order size, 
        # then we can't order in integer sizes. We must order in fractional sizes
        base_order_size = size if size != 0 else self.params.dca_base_order_size_usd/entry_price
        
        buy_order = self.buy(size=base_order_size, exectype=bt.Order.Market)
        self.safety_orders.append(buy_order)
        self.is_dca = True
        return

    def __buy_and_hold(self) -> None:
        if self.hullma[0] - self.hullma[-1] > 0: # this 200 number is subject, moving upwards (sell -> buy)
            entry_price     = self.data.close[0]
            base_order_size = (self.broker.get_cash() / self.data.close[0]) * 0.98
            self.buy(price=entry_price, size=base_order_size, exectype=bt.Order.Market)
            self.is_dca     = False
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            order_executed_size  = '{:,.8f}'.format(order.executed.size)
            order_executed_price = '{:,.8f}'.format(order.executed.price)
            order_executed_value = '{:,.8f}'.format(order.executed.value)
            order_executed_comm  = '{:,.8f}'.format(order.executed.comm)
            date                 = self.data.datetime.date()
            minutes              = self.datas[0].datetime.time(0)            
            
            if order.isbuy():
                print(f"[{date} {minutes}] BUY EXECUTED, Size: {order_executed_size} Price: {order_executed_price}, Cost: {order_executed_value}, Comm {order_executed_comm}")
                
                if order.exectype == 0:
                    if not self.is_dca:
                        """Buy&Hold take profit order"""
                        entry_price       = order.executed.price
                        base_order_size   = order.executed.size
                        take_profit_price = entry_price + (entry_price * (self.params.bh_target_profit_percent/100))

                        self.bh_take_profit_order = self.sell(price=take_profit_price,
                                                              size=base_order_size,
                                                            # trailpercent=self.params.bh_trail_percent,
                                                            # plimit=take_profit_price,
                                                            # exectype=bt.Order.StopTrailLimit)
                                                              exectype=bt.Order.Limit)
                    else:
                        """ DCA """
                        entry_price     = order.executed.price
                        base_order_size = order.executed.size
                        size            = self.params.dca_safety_order_size_usd

                        # If the cost of the stock/coin is larger than our base order size,
                        # then we can't order in integer sizes. We must order in fractional sizes
                        safety_order_size = size//entry_price if size//entry_price != 0 else size/entry_price

                        self.dca = DCA(entry_price_usd=entry_price,
                                       target_profit_percent=self.params.dca_target_profit_percent,
                                       safety_orders_max=self.params.dca_safety_orders_max,
                                       safety_orders_active_max=self.params.dca_safety_orders_active_max,
                                       safety_order_volume_scale=self.params.dca_safety_order_volume_scale,
                                       safety_order_step_scale=self.params.dca_safety_order_step_scale,
                                       safety_order_price_deviation_percent=self.params.dca_safety_order_price_deviation,
                                       base_order_size=base_order_size,
                                       safety_order_size=safety_order_size,
                                       total_usd=self.broker.get_cash())
                        
                        self.safety_order_sizes_usd.append(self.dca.safety_order_size_usd)

                        take_profit_price = self.dca.base_order_required_price

                        # BASE ORDER SELL (TAKE PROFIT: if this sell is filled, cancel all the other safety orders)
                        self.dca_take_profit_order = self.sell(price=take_profit_price,
                                                            size=base_order_size,
                                                            trailpercent=self.params.dca_trail_percent,
                                                            plimit=take_profit_price,
                                                            exectype=bt.Order.StopTrailLimit)

                        """instead of submitting the takeprofit and all safety orders at a single time,
                        submit one safety order and one take profit order until one of them is canceled!"""
                        safety_order = self.buy(price=self.dca.price_levels[0],
                                                size=self.dca.safety_order_quantity_levels[0],
                                                exectype=bt.Order.Limit,
                                                oco=self.dca_take_profit_order) # oco = One Cancel Others

                        self.safety_orders.append(safety_order)
            elif order.issell():
                print(f"[{date} {minutes}] SELL EXECUTED, Size: {order_executed_size} Price: {order_executed_price}, Cost: {order_executed_value}, Comm {order_executed_comm}")
                
                # reset variables
                if self.is_dca:
                    self.safety_orders         = []
                    self.dca_take_profit_order = None
                    self.is_first_safety_order = True
                else:
                    self.bh_take_profit_order = None
        elif order.status in [order.Canceled]:
            # if the sell was canceled, that means a safety order was filled and its time to put in a new updated take profit order.
            self.log(f'ORDER CANCELED: Size: {order.size}')

            if self.is_dca:
                if order.issell():
                    self.__dca_set_take_profit()
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
            self.log('TRADE COMPLETE, GROSS %.6f, NET %.6f, Size: %.6f' % (trade.pnl, trade.pnlcomm, trade.size))

            # if trade.pnl <= 0 or trade.pnlcomm <= 0:
            #     print(trade.pnl, trade.pnlcomm)
            #     print()
            #     print(trade)
            #     print()
        return

    def prenext(self) -> None:
        print(f"Prenext: {self.prenext_count} \\ {self.prenext_total} {round((self.prenext_count/self.prenext_total)*100)}%\r", end='')
        self.prenext_count += 1
        return

    def next(self) -> None:
        self.print_ohlc()
        current_price = self.data.close[0]
            
        if current_price > self.sma[0] and self.bh_take_profit_order is None and len(self.safety_orders) == 0:
            self.__buy_and_hold()
        elif current_price < self.sma[0]:
            if len(self.safety_orders) == 0 and self.bh_take_profit_order is None and len(self.safety_orders) == 0:
                self.__dca_start_new_deal()
        return

    def start(self) -> None:
        self.prenext_total = max(self._minperiods) * 60 * 24 # number of minutes in 200 days
        self.time_period   = self.datas[0].p.todate - self.datas[0].p.fromdate
        self.start_cash    = self.broker.get_cash()
        self.start_value   = self.broker.get_value()
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

        print('target_profit_percent:         ', self.params.dca_target_profit_percent)
        print('trail_percent:                 ', self.params.dca_trail_percent)
        print('safety_orders_max:             ', self.params.dca_safety_orders_max)
        print('safety_orders_active_max:      ', self.params.dca_safety_orders_max)
        print('safety_order_volume_scale:     ', self.params.dca_safety_order_volume_scale)
        print('safety_order_step_scale:       ', self.params.dca_safety_order_step_scale)
        print('safety_order_price_deviation:  ', self.params.dca_safety_order_price_deviation)
        print('base_order_size_usd:           ', self.params.dca_base_order_size_usd)

        if len(self.safety_order_sizes_usd) > 0:
            if min(self.safety_order_sizes_usd) == max(self.safety_order_sizes_usd):
                print(f'safety_order_size_usd:          {min(self.safety_order_sizes_usd)}')
            else:
                print(f'safety_order_sizes_usd:         {min(self.safety_order_sizes_usd)} - {max(self.safety_order_sizes_usd)}')

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
    
    period_results = dict()

    for period in range(1, 11): # PERIOD 1-10
        start_date, end_date = get_period(period)
        start_date -= datetime.timedelta(days=200) # time required to process the 200 day simple moving average

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
        
        cerebro.addstrategy(BHDCA)

        cerebro.addindicator(bt.indicators.HullMovingAverage,   period=20)
        cerebro.addindicator(bt.indicators.MovingAverageSimple, period=200)

        p = period

        print()
        print("^^^^ STARTING THE BACKTEST ^^^^^")
        print(f"*** Testing period {p} ***")
        print()

        cerebro.run()

        # b = Bokeh(style='bar', filename='backtest_results/HullMA.html', output_mode='show', scheme=Blackly())
        # cerebro.plot(b)
        # break

    for period, roi in period_results.items():
        print(f"period: {period}, roi: {roi}")

