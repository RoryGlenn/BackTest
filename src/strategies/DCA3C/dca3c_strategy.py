# Dollar Cost Averaging Strategy
    # https://community.backtrader.com/topic/4010/dollar-cost-averaging-strategy/15

from __future__ import (absolute_import, division, print_function, unicode_literals)
from dca        import DCA

import os
import backtrader as bt
import pandas     as pd


STARTING_CASH = 1000000
ORACLE        = "historical_data/oracle.csv"

# TODO:
    #  CAN WE FORCE THE CANDLESTICK LOWS TO HAPPEN BEFORE THE CANDLESTICK HIGHS?
    # Store data in db?


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

        self.dca                   = None
        self.has_base_order_filled = False
        return

    def print_safety_orders(self) -> None:
        if self.dca is not None:
            print()
            self.dca.print_table()
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

        # If a sell order has already been made, cancel it
        # self.cancel(self.take_profit_order)

        print()
        print("CANCELED TAKE PROFIT SELL ORDER")
        print(f"Price: {self.take_profit_order.price}, Size: {self.take_profit_order.size}")

        # total_quantity = self.dca.total_quantities.pop(0)
        # required_price = self.dca.required_price_levels.pop(0)

        self.dca.print_table()
        
        quantity_to_sell = self.dca.total_quantities[0]
        required_price   = self.dca.required_price_levels[0]

        self.take_profit_order = self.sell(price=required_price,
                                           size=quantity_to_sell,
                                           exectype=bt.Order.Limit)

        safety_order = self.buy(price=self.dca.price_levels[0],
                                    size=self.dca.quantities[0],
                                    exectype=bt.Order.Limit,
                                    oco=self.take_profit_order) # oco = One Cancel Others
        
        self.safety_orders.append(safety_order)

        self.dca.remove_top_safety_order()
        
        print()
        print("NEW TAKE PROFIT ORDER")
        print(f"Price: {self.take_profit_order.price}, Size: {self.take_profit_order.size}")
        print()
        return

    def notify_order(self, order: bt.order.BuyOrder):
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
                
                self.buyprice = order.executed.price
                self.buycomm  = order.executed.comm

                # Update current deal variables
                # self.has_position = True

                # # Update the sell order take profit price every time a new safety order is filled
                # if self.has_base_order_filled:
                #     self.set_take_profit()
                # else:
                #     self.has_base_order_filled = True

                """
                In order to place and cancel order on time, we need to look at the next day and see which buy/sell orders will be filled

                If a sell is to be filled the next day, cancel all buy orders below the sell price
                
                """

            elif order.issell():
                self.log('SELL EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))

                self.print_orders()

                # Cancel all of the unfilled safety orders
                # [self.cancel(order) for order in self.safety_orders]

                # Clear the list to store orders for the next deal
                self.safety_orders = []

                # Clear variable to store new sell order (TP)
                self.take_profit_order     = None
                self.has_base_order_filled = False
        elif order.status in [order.Canceled]:
            self.log('ORDER CANCELED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            
            # if the sell was canceled, that means a safety order was filled. 
            # time to put in a new take profit order
            if order.ordtype == 1: # if the canceled order was a sell (aka. the take profit order)
                self.set_take_profit()
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
        self.order = None
        return

    def notify_trade(self, trade: bt.trade.Trade) -> None:
        if trade.isclosed:
            self.log('OPERATION PROFIT, GROSS %.6f, NET %.6f, Size: %.6f' % (trade.pnl, trade.pnlcomm, trade.size))
        return

    def operate(self) -> None:
        if self.position.size == 0:
            print('{} OPERATE: send Buy, close {}'.format(self.data.datetime.date(), self.data.close[0]))

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
            buy_order = self.buy(price=entry_price, size=self.params.base_order_size)
            self.safety_orders.append(buy_order)

            # BASE ORDER SELL (if this sell is filled, cancel all the other safety orders)
            tp_price = entry_price + ( entry_price * (self.params.target_profit_percent/100) )
            
            self.take_profit_order = self.sell(price=tp_price,
                                               size=self.params.base_order_size,
                                               exectype=bt.Order.Limit)

            # SAFETY ORDERS (if any of these orders are filled, cancel any open sell order/takeprofit order)
            # for i in range(self.dca.safety_orders_active_max):
            #     buy_order = self.buy(price=self.dca.price_levels[i],
            #                          size=self.dca.quantities[i],
            #                          exectype=bt.Order.Limit,
            #                          oco=self.take_profit_order) # oco = One Cancel Others
            #     self.safety_orders.append(buy_order)

            """instead of submitting the takeprofit and all safety orders at a single time,
            submit one safety order and one take profit order until one of thme is canceled!"""
            safety_order = self.buy(price=self.dca.price_levels[0],
                                        size=self.dca.quantities[0],
                                        exectype=bt.Order.Limit,
                                        oco=self.take_profit_order) # oco = One Cancel Others

            self.safety_orders.append(safety_order)

            self.dca.remove_top_safety_order()
            # self.print_orders()
        return

    def next(self) -> None:
        print("\n-> NEXT ->")
        print(f"{self.data.datetime.date()} next, Open: {self.data.open[0]}, High: {self.data.high[0]}, Low: {self.data.low[0]}, Close: {self.data.close[0]}")
        self.operate()
        return

    def stop(self) -> None:
        print()
        print("Finished Backtesting")
        profit = round(cerebro.broker.getvalue() - starting_value, 2)
        print(f"Final Portfolio Value: ${round(cerebro.broker.getvalue(), 2)}")
        print(f"Total Profit: ${profit}")
        return



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
    cerebro.addstrategy(DCA3C)

    starting_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: {starting_value}")

    cerebro.run()
    cerebro.plot(volume=False, style='candlestick')
