# Dollar Cost Averaging Strategy
    # https://community.backtrader.com/topic/4010/dollar-cost-averaging-strategy/15

from __future__ import (absolute_import, division, print_function, unicode_literals)
from dca        import DCA

import os
import backtrader as bt
import pandas     as pd
from buy_and_hold import BuyAndHold
import math

STARTING_CASH = 1000000
ORACLE        = "historical_data/oracle.csv"
BNGO          = "historical_data/BNGO.csv"

# PULL DATA FROM CRYPTO FUTURES TO SEE WHEN LIQUIDATION OCCURES
# Time frames: Buy and hold might win out in the long run, but what time frames does DCA when out?


class DCA3C(bt.Strategy):
    # DCA values
    params = (
        ('target_profit_percent',        1),
        ('safety_orders_max',            7),
        ('safety_orders_active_max',     7),
        ('safety_order_volume_scale',    2.5),
        ('safety_order_step_scale',      1.56),
        ('safety_order_price_deviation', 1.3),
        ('base_order_size_usd',          8100), # in terms of USD
        ('safety_order_size_usd',        4050), # in terms of USD
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

        self.starting_value = 0

        self.data_open  = self.datas[0].open
        self.data_high  = self.datas[0].high
        self.data_low   = self.datas[0].low
        self.data_close = self.datas[0].close

        # Store the sell order (take profit) so we can cancel and update tp price with ever filled SO
        self.take_profit_order = None
        
        # Store all the Safety Orders so we can cancel the unfilled ones after TPing
        self.safety_orders = []
        # self.order                 = None
        self.dca                   = None
        self.has_base_order_filled = False
        self.is_first_safety_order = True
        return

    def print_orders(self) -> None:
        print()
        for order in self.safety_orders:
            print(f"Price: {order.price} Quantity: {order.size}, Status: {order.status}, Alive: {order.alive()}")  
        return

    def set_take_profit(self) -> None:
        '''
        Function to update the take profit order when new safety orders are placed
        '''

        if self.take_profit_order is None:
            return

        if self.take_profit_order.status in [self.take_profit_order.Completed]:
            return

        print()
        print("CANCELED TAKE PROFIT SELL ORDER")
        print(f"Price: {self.take_profit_order.price}, Size: {self.take_profit_order.size}")
        
        # self.dca.print_table()

        if self.is_first_safety_order:
            self.is_first_safety_order = False
            quantity_to_sell = self.dca.total_quantities[0]
            required_price   = self.dca.required_price_levels[0]

            self.take_profit_order = self.sell(price=required_price,
                                            size=quantity_to_sell,
                                            exectype=bt.Order.Limit)
            # print(self.take_profit_order)

            # IS QUANTITY_TO_SELL DIFFERENT THAN SELF.POSITION.SIZE??????????????????????????
            print("quantity_to_sell", quantity_to_sell)
            print("self.position.size", self.position.size)

            
            self.dca.remove_top_safety_order()
            
            safety_order = self.buy(price=self.dca.price_levels[0],
                                        size=self.dca.quantities[0],
                                        exectype=bt.Order.Limit,
                                        oco=self.take_profit_order) # oco = One Cancel Others
            # print(safety_order)
        else:
            quantity_to_sell = self.dca.total_quantities[0]
            
            self.dca.remove_top_safety_order()
            
            required_price   = self.dca.required_price_levels[0]

            self.take_profit_order = self.sell(price=required_price,
                                            size=quantity_to_sell,
                                            exectype=bt.Order.Limit)


            # IS QUANTITY_TO_SELL DIFFERENT THAN SELF.POSITION.SIZE??????????????????????????
            print("quantity_to_sell", quantity_to_sell)
            print("self.position.size", self.position.size)

            # print(self.take_profit_order)
            
            safety_order = self.buy(price=self.dca.price_levels[0],
                                        size=self.dca.quantities[0],
                                        exectype=bt.Order.Limit,
                                        oco=self.take_profit_order) # oco = One Cancel Others
            # print(safety_order)
        
        self.safety_orders.append(safety_order)
        
        print()
        print("NEW TAKE PROFIT ORDER")
        print(f"Price: {self.take_profit_order.price}, Size: {self.take_profit_order.size}")
        print()
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm  = order.executed.comm
                # self.has_base_order_filled = True
            elif order.issell():
                self.log('SELL EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                
                # make sure this works....(is position.size == 0 after this call?)
                self.position.close()

                # Clear the list to store orders for the next deal
                self.safety_orders = []

                # Clear variable to store new sell order (TP)
                self.take_profit_order     = None
                self.has_base_order_filled = False
                self.is_first_safety_order = True
        elif order.status in [order.Canceled]:
            # print(order.ordtype)
            self.log(f'ORDER CANCELED: Size: {order.size}')
            # if the sell was canceled, that means a safety order was filled. 
            # time to put in a new take profit order
            if order.issell(): # if the canceled order was a sell (aka. the take profit order)
                self.set_take_profit()
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.size, order.price, order.value, order.comm))
        # self.order = None
        return

    def notify_trade(self, trade: bt.trade.Trade) -> None:
        if trade.isclosed:
            self.log('OPERATION PROFIT, GROSS %.6f, NET %.6f, Size: %.6f' % (trade.pnl, trade.pnlcomm, trade.size))
        return

    def operate(self) -> None:

    #  for some reason, the full quantity of our stocks is not being sold...wtf???

        if len(self.safety_orders) == 0: 
            print('{} OPERATE: send Buy, close {}'.format(self.data.datetime.date(), self.data.close[0]))

            entry_price = self.data.close[0]

            print('')
            print('*** NEW DEAL ***')

            self.dca = DCA(entry_price,
                           self.params.target_profit_percent,
                           self.params.safety_orders_max,
                           self.params.safety_orders_active_max,
                           self.params.safety_order_volume_scale,
                           self.params.safety_order_step_scale, 
                           self.params.safety_order_price_deviation,
                           self.params.base_order_size_usd/entry_price,
                           self.params.safety_order_size_usd/entry_price)
            self.dca.start()
            # self.dca.print_table()

            # BASE ORDER BUY
            buy_order = self.buy(price=entry_price, size=self.params.base_order_size_usd/entry_price)
            self.safety_orders.append(buy_order)

            # BASE ORDER SELL (if this sell is filled, cancel all the other safety orders)
            tp_price = entry_price + ( entry_price * (self.params.target_profit_percent/100) )
            
            self.take_profit_order = self.sell(price=tp_price,
                                               size=self.params.base_order_size_usd/entry_price,
                                               exectype=bt.Order.Limit)

            """instead of submitting the takeprofit and all safety orders at a single time,
            submit one safety order and one take profit order until one of them is canceled!"""
            safety_order = self.buy(price=self.dca.price_levels[0],
                                        size=self.dca.quantities[0],
                                        exectype=bt.Order.Limit,
                                        oco=self.take_profit_order) # oco = One Cancel Others

            self.safety_orders.append(safety_order)
        return

    def next(self) -> None:
        print("\n-> NEXT ->")
        print(f"{self.data.datetime.date()} next, Open: {self.data.open[0]}, High: {self.data.high[0]}, Low: {self.data.low[0]}, Close: {self.data.close[0]}")
        self.operate()
        return

    def start(self) -> None:
        self.starting_value = self.broker.getvalue()
        print(f"Starting Portfolio Value: {self.starting_value}")
        return

    def stop(self) -> None:
        profit = round(self.broker.getvalue() - self.starting_value, 2)

        print("\n^^^^ Finished Backtesting ^^^^^")
        print(f"Final Portfolio Value: ${round(self.broker.getvalue(), 2)}")
        print(f"Total Profit: ${profit}")
        return

    def round_decimals_down(self, number: float, decimals: int = 2) -> int | float:
        """Returns a value rounded down to a specific number of decimal places."""
        if not isinstance(decimals, int):
            raise TypeError("decimal places must be an integer")
        elif decimals < 0:
            raise ValueError("decimal places has to be 0 or more")
        elif decimals == 0:
            return math.floor(number)
        factor = 10 ** decimals
        return math.floor(number * factor) / factor




if __name__ == '__main__':
    os.system("cls")

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(ORACLE)
    df.drop(columns=["Volume", "Adj Close"], inplace=True)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    data = bt.feeds.PandasData(dataname=df, openinterest=-1, volume=-1)

    cerebro.adddata(data)
    # cerebro.addstrategy(DCA3C)
    cerebro.addstrategy(BuyAndHold)

    cerebro.run()
    cerebro.plot(volume=False)


    #############################
    # ('target_profit_percent',        1),
    # ('safety_orders_max',            7),
    # ('safety_orders_active_max',     7),
    # ('safety_order_volume_scale',    2.5),
    # ('safety_order_step_scale',      1.56),
    # ('safety_order_price_deviation', 1.3),
    # ('base_order_size_usd',          8100), # in terms of USD
    # ('safety_order_size_usd',        4050), # in terms of USD

    # Finished Backtesting
    # Final Portfolio Value: $1019720.15
    # Total Profit: $19720.15
    #############################


