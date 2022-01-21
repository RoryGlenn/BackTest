from __future__ import (absolute_import, division, print_function, unicode_literals)
from strategies.dca        import DCA, DECIMAL_MAX
from pprint     import pprint

import backtrader as bt


"""
CURRENT PROBLEM!
    after a sell order is executed, the open buy orders are NOT cancelled?

"""

class DCAStrategy(bt.Strategy):
    def __init__(self) -> None:
        # Sentinel to None: new ordersa allowed
        self.order: bt.order.BuyOrder          = None

        # DCA values
        self.dca_target_profit_percent:        float = 1.0
        self.dca_safety_orders_max:            int   = 7
        self.dca_safety_orders_active_max:     int   = 7
        self.dca_safety_order_volume_scale:    float = 2.5
        self.dca_safety_order_step_scale:      float = 1.56
        self.dca_safety_order_price_deviation: float = 1.3
        self.dca_base_order_size:              float = 10
        self.dca_safety_order_size:            float = 10
        
        self.dca:                              DCA   = None

        self.open_safety_orders:               list  = []
        return

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))
        return

    def notify_trade(self, trade) -> None:
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f, Size: %.5f' %
                 (trade.pnl, trade.pnlcomm, trade.size))
        print(self.position)
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        # if order.status in [order.Submitted]:
        #     # Buy/Sell order submitted/accepted to/by broker - Nothing to do
        #     self.log('ORDER SUBMITTED', dt=order.created.dt)
        #     self.order = order
        # elif order.status in [order.Accepted]:
        #     # Buy/Sell order submitted/accepted to/by broker - Nothing to do
        #     self.log('ORDER ACCEPTED', dt=order.created.dt)
        #     self.order = order
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY FILLED, Price: %.8f, Cost: %.8f, Comm %.8f' % (order.executed.price, order.executed.value, order.executed.comm))
                # the safety order was filled, remove it from open_safety_orders
                if order in self.open_safety_orders:
                    self.open_safety_orders.remove(order)
            elif order.issell():
                self.log('SELL FILLED, Price: %.8f, Cost: %.8f, Comm %.8f' % (order.executed.price, order.executed.value, order.executed.comm))

                # cancel all open safety orders
                for _order in self.open_safety_orders:
                    # how do we check if a buy order was filled?

                    # print(_order.ref)
                    # print(_order.ordtype)
                    # print(_order.ordtypename())
                    # print(_order.status)
                    # print(_order.getstatusname())
                    # print(_order.size)
                    # print(_order.price)
                    # print(_order.pricelimit)
                    # print(_order.trailamount)
                    # print(_order.trailpercent)
                    # print(_order.exectype)
                    # print(_order.getordername())
                    # print(_order.comminfo)
                    # print(_order.dteos)
                    # print(_order.info)
                    # print(_order.broker)
                    # print(_order.alive())
                    # print()

                    self.cancel(_order)
                
                if self.position:
                    print(self.position)
                
                # reset variables
                self.dca                = None
                self.open_safety_orders = []
        elif order.status in [order.Expired]:
            self.log('BUY EXPIRED')

        # Sentinel to None: new orders allowed
        self.order = None
        return

    def next(self) -> None:
        if self.order:
            # pending order ... do nothing
            return

        if self.position:
            # Check if we are in the market
            # print(self.position)
            return

        entry_price = self.data.close[0]

        # how much coin can we get for self.dca_base_order_size?
        base_order_quantity = round(self.dca_base_order_size/entry_price, DECIMAL_MAX)

        # BASE ORDER MARKET BUY
        self.buy(size=base_order_quantity,
                    price=None,
                    exectype=bt.Order.Market) # for market order (price=float for limit order)

        self.dca = DCA(entry_price,
                        self.dca_target_profit_percent,
                        self.dca_safety_orders_max,
                        self.dca_safety_orders_active_max,
                        self.dca_safety_order_volume_scale,
                        self.dca_safety_order_step_scale,
                        self.dca_safety_order_price_deviation,
                        self.dca_base_order_size,
                        self.dca_safety_order_size)
        
        self.dca.start()

        base_order_required_price = entry_price + (entry_price * self.dca_target_profit_percent/100)
        base_order_required_price = round(base_order_required_price, DECIMAL_MAX)

        # BASE ORDER SELL
        self.sell(size=base_order_quantity,
                  price=base_order_required_price, 
                  exectype=bt.Order.Limit)
        
        # SAFETY ORDERS
        for i in range(self.dca.safety_orders_active_max):
            buy_order = self.buy(size=self.dca.quantities[i],
                                 price=self.dca.price_levels[i],
                                 exectype=bt.Order.Limit)
            
            self.open_safety_orders.append(buy_order)
        
        # for order in self.open_safety_orders:
        #     print(order)
        #     print()
        return
