from __future__ import (absolute_import, division, print_function, unicode_literals)
from dca        import DCA

import backtrader as bt

import time
import math
import sys


BTCUSD_DECIMAL_PLACES = 5


class BHDCA(bt.Strategy):
    params = (
        ('bh_target_profit_percent', 1), 
        ('bh_trail_percent',         0.01), # 1%
        

        # rename all of these to DCA_...
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
        self.hullma_20_day = bt.indicators.HullMovingAverage(self.datas[1],   period=20)
        self.ma_200_day    = bt.indicators.MovingAverageSimple(self.datas[1], period=200)

        # self.hullma = bt.indicators.HullMovingAverage(self.datas[0],   period=20)
        # self.sma    = bt.indicators.MovingAverageSimple(self.datas[0], period=200)

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

        # print("\nCANCELED TAKE PROFIT SELL ORDER")
        # print(f"Price: {self.money_format(self.take_profit_order.price)}, Size: {self.take_profit_order.size}\n")

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
        
        # print("\nNEW TAKE PROFIT ORDER")
        # print(f"Price: {self.money_format(self.take_profit_order.price)}, Size: {self.take_profit_order.size}")
        # print()
        return

    def __dca_start_new_deal(self) -> None:
        # print("\n*** NEW DEAL ***")

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
        if self.hullma[0] - self.hullma[-1] > 200: # this 200 number is subject, moving upwards (sell -> buy)
            entry_price     = self.data.close[0]
            base_order_size = (self.broker.get_cash() / self.data.close[0]) * 0.97
            self.buy(price=entry_price, size=base_order_size, exectype=bt.Order.Market)
            self.is_dca     = False
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: {:,.8f} Price: {:,.8f}, Cost: {:,.8f}, Comm {:,.8f}'.format(order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                
                if order.exectype == 0:
                    if not self.is_dca:
                        """Buy&Hold take profit order"""
                        entry_price       = order.executed.price
                        base_order_size   = order.executed.size
                        take_profit_price = entry_price + (entry_price * self.params.bh_target_profit_percent/100)

                        self.bh_take_profit_order = self.sell(price=take_profit_price,
                                                            size=base_order_size,
                                                            trailpercent=self.params.bh_trail_percent,
                                                            plimit=take_profit_price,
                                                            exectype=bt.Order.StopTrailLimit)
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
                self.log('SELL EXECUTED, Size: {:,.8f} Price: {:,.8f}, Cost: {:,.8f}, Comm {:,.8f}'.format(order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                
                # if self.position.size != 0:
                #     print()
                #     print(self.position)
                #     print()
                
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
            self.log('OPERATION PROFIT, GROSS %.6f, NET %.6f, Size: %.6f' % (trade.pnl, trade.pnlcomm, trade.size))

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
        total_value = self.broker.get_value()
        profit      = total_value - self.start_cash
        roi         = ((total_value / self.start_cash) - 1.0) * 100
        roi         = '{:.2f}%'.format(roi)

        profit           = self.money_format(round(profit, 2))
        self.start_value = self.money_format(round(self.start_value, 2))
        total_value      = self.money_format(round(total_value, 2))

        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print("##########################################")
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
        return
