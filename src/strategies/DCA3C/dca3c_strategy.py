# Dollar Cost Averaging Strategy
    # https://community.backtrader.com/topic/4010/dollar-cost-averaging-strategy/15

from __future__ import (absolute_import, division, print_function, unicode_literals)
from dca        import DCA

import datetime
import os

import backtrader as bt
import pandas as pd


STARTING_CASH = 1000000
ORACLE        = "historical_data/oracle.csv"

#  CAN WE FORCE THE CANDLESTICK LOWS TO HAPPEN BEFORE THE CANDLESTICK HIGHS?

class DCA3C(bt.Strategy):
    # DCA values
    params = (
        ('target_profit_percent',        1.0),
        ('safety_orders_max',            7),
        ('safety_orders_active_max',     7),
        ('safety_order_volume_scale',    2.5),
        ('safety_order_step_scale',      1.56),
        ('safety_order_price_deviation', 1.3),
        ('base_order_size',              10),
        ('safety_order_size',            5),
    )

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        
        if isinstance(dt, float):
            dt = bt.num2date(dt)

        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return


    def __init__(self) -> None:
        # Update TP to include making back the commission
        # self.params.tp += commission
        
        self.data_open  = self.datas[0].open
        self.data_high  = self.datas[0].high
        self.data_low   = self.datas[0].low
        self.data_close = self.datas[0].close


        # Store the sell order (take profit) so we can cancel and update tp price with ever filled SO
        self.take_profit_order = None
        
        # Store all the Safety Orders so we can cancel the unfilled ones after TPing
        self.safety_orders = []
        self.order         = None

        self.cheating: bool = self.cerebro.p.cheat_on_open

        self.dca                   = None
        self.has_position          = False
        self.has_base_order_filled = False
        return


    def notify_order(self, order: bt.order.BuyOrder):
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm  = order.executed.comm

                # Update current deal variables
                self.has_position = True

                # if self.has_base_order_filled:
                #     filled_orders = [_order for _order in self.orders if not _order.alive() and order.exectype != 0]
                #     total_quantity = 0
                #     required_price = 0

                #     for _order in filled_orders:
                #         total_quantity = self.dca.total_quantities.pop(0)
                #         required_price = self.dca.required_price_levels.pop(0)

                    # self.take_profit_order = self.sell(price=required_price,
                    #                                    size=total_quantity,
                    #                                    exectype=bt.Order.Limit)

                # else:
                #     self.has_base_order_filled = True

                # Update the sell order take profit price every time a new safety order is filled
                if self.has_base_order_filled:
                    self.set_take_profit()
                else:
                    self.has_base_order_filled = True

            elif order.issell():  # Sell
                self.log('SELL EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))

                # Cancel all of the unfilled safety orders
                [self.cancel(order) for order in self.safety_orders]

                # Clear the list to store orders for the next deal
                self.safety_orders = []

                # Clear variable to store new sell order (TP)
                self.take_profit_order     = None
                self.has_position          = False
                self.has_base_order_filled = False

        # Debugging
        # elif order.status in [order.Canceled, order.Margin, order.Rejected]:
        elif order.status in [order.Margin]:
            self.log('Order Margin')
            print(order)
        return

    def notify_trade(self, trade: bt.trade.Trade) -> None:
        if trade.isclosed:
            self.log('OPERATION PROFIT, GROSS %.6f, NET %.6f, Size: %.6f' % (trade.pnl, trade.pnlcomm, trade.size))
        return

    def set_take_profit(self) -> None:
        '''
        Function to update the take profit order when new safety orders are placed
        '''

        if self.take_profit_order is None:
            return

        if self.take_profit_order.status in [self.take_profit_order.Completed]:
            return

        # If a sell order has already been made, cancel it
        self.cancel(self.take_profit_order)

        print()
        print("CANCELED TAKE PROFIT SELL ORDER")
        print(f"Price: {self.take_profit_order.price}, Size: {self.take_profit_order.size}")

        total_quantity = self.dca.total_quantities.pop(0)
        required_price = self.dca.required_price_levels.pop(0)

        self.take_profit_order = self.sell(price=required_price,
                                           size=total_quantity,
                                           exectype=bt.Order.Limit)

        print()
        print("NEW TAKE PROFIT ORDER")
        print(f"Price: {self.take_profit_order.price}, Size: {self.take_profit_order.size}")
        print()
        return

    def next_open(self) -> None:
        """
        https://www.backtrader.com/blog/posts/2017-05-01-cheat-on-open/cheat-on-open/
        If cheat-on-open is True, it will only operate from next_open
        If cheat-on-open is False, it will only operate from next

        In both cases the matching price must be the same
        If not cheating, the order is issued at the end of the previous day and will be matched with the next incoming price which is the open price
        If cheating, the order is issued on the same day it is executed. 
        Because the order is issued before the broker has evaluated orders, it will also be matched with the next incoming price, the open price.
        This second scenario, allows calculation of exact stakes for all-in strategies, because one can directly access the current open price.

        In both cases
        The current open and close prices will be printed from next. 
        
        """
        print("\n-> NEXT_OPEN CANDLE STICK ->")
        print(f"{self.data.datetime.date()} next open, Open: {self.data.open[0]}, High: {self.data.high[0]}, Low: {self.data.low[0]}, Close: {self.data.close[0]}")

        if not self.cheating:
            return

        # self.operate(fromopen=True) # why doesn't this work??

        if self.position.size == 0:
            print('')
            print('*** NEW DEAL ***')
            entry_price = self.data_open[0]

            self.dca = DCA(entry_price,
                           self.params.target_profit_percent,
                           self.params.safety_orders_max,
                           self.params.safety_orders_active_max,
                           self.params.safety_order_volume_scale,
                           self.params.safety_order_step_scale, 
                           self.params.safety_order_price_deviation,
                           self.params.base_order_size, 
                           self.params.safety_order_size)
            self.dca.start()
            # self.dca.print_table()

            # BASE ORDER BUY
            buy_order = self.buy(price=entry_price,
                                 size=self.params.base_order_size)
            self.safety_orders.append(buy_order)

            # BASE ORDER SELL         
            self.take_profit_order = self.sell(price=entry_price + (entry_price * (self.params.target_profit_percent/100)),
                                               size=self.params.base_order_size,
                                               exectype=bt.Order.Limit)

            # SAFETY ORDERS
            for i in range(self.dca.safety_orders_active_max):
                buy_order = self.buy(price=self.dca.price_levels[i],
                                     size=self.dca.quantities[i],
                                     exectype=bt.Order.Limit)
                self.safety_orders.append(buy_order)
        return

    def nextstart_open(self) -> None:
        print("\n-> NEXT_START ->")
        print(f"{self.data.datetime.date()} next start open, Open: {self.data.open[0]}, High: {self.data.high[0]}, Low: {self.data.low[0]}, Close: {self.data.close[0]}")        
        return 

    def prenext_open(self) -> None:
        print("\n-> PRE_NEXT_OPEN ->")
        print(f"{self.data.datetime.date()} pre next open, Open: {self.data.open[0]}, High: {self.data.high[0]}, Low: {self.data.low[0]}, Close: {self.data.close[0]}")
        return

    # def next(self):
    #     print("\n-> NEXT ->")
    #     print(f"{self.data.datetime.date()} next, Open: {self.data.open[0]}, High: {self.data.high[0]}, Low: {self.data.low[0]}, Close: {self.data.close[0]}")

    #     # print("\n-> NEXT CANDLE STICK ->")
    #     # self.log('Open, %.6f' % self.data_close[0]) # this is a rounded number

    #     if self.cheating:
    #         # this will take us to nextstart_open()
    #         return
        
    #     # self.operate(fromopen=False)

    #     # If we are not in the market start the next deal
    #     # if not self.has_position:
    #     if self.position.size == 0:
    #         print('')
    #         print('*** NEW DEAL ***')
    #         # entry_price = self.price[0]
    #         entry_price = self.data_open[0]

    #         self.dca = DCA(entry_price,
    #                        self.params.target_profit_percent,
    #                        self.params.safety_orders_max,
    #                        self.params.safety_orders_active_max,
    #                        self.params.safety_order_volume_scale,
    #                        self.params.safety_order_step_scale, 
    #                        self.params.safety_order_price_deviation,
    #                        self.params.base_order_size, 
    #                        self.params.safety_order_size)
    #         self.dca.start()
    #         # self.dca.print_table()

    #         # BASE ORDER BUY
    #         buy_order = self.buy(price=entry_price,
    #                              size=self.params.base_order_size)
    #         self.safety_orders.append(buy_order)

    #         # BASE ORDER SELL         
    #         self.take_profit_order = self.sell(price=entry_price + (entry_price * (self.params.target_profit_percent/100)),
    #                                            size=self.params.base_order_size,
    #                                            exectype=bt.Order.Limit)

    #         # SAFETY ORDERS
    #         for i in range(self.dca.safety_orders_active_max):
    #             buy_order = self.buy(price=self.dca.price_levels[i],
    #                                  size=self.dca.quantities[i],
    #                                  exectype=bt.Order.Limit)
    #             self.safety_orders.append(buy_order)
    #     return

    def stop(self) -> None:
        print("Finished Backtesting")
        return



if __name__ == '__main__':
    os.system("cls")

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df         = pd.read_csv(ORACLE)
    df.drop(columns=["Volume", "Adj Close"], inplace=True)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    data = bt.feeds.PandasData(dataname=df, openinterest=-1, volume=-1)

    cerebro.adddata(data)
    cerebro.addstrategy(DCA3C)

    starting_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: {starting_value}")
    cerebro.run(cheat_on_open=True)

    print()
    profit = round(cerebro.broker.getvalue() - starting_value, 2)
    print(f"Final Portfolio Value: ${round(cerebro.broker.getvalue(), 2)}")
    print(f"Total Profit: ${profit}")
    cerebro.plot(volume=False, style='candlestick')
