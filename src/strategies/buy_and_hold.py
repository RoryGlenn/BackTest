from __future__ import (absolute_import, division, print_function, unicode_literals)


import backtrader as bt
import time


class BuyAndHold(bt.Strategy):
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

        self.start_time = time.time()

        # Store the sell order (take profit) so we can cancel and update tp price with ever filled SO
        self.take_profit_order = None
        
        # Store all the Safety Orders so we can cancel the unfilled ones after TPing
        self.safety_orders         = []

        self.dca                   = None
        self.is_first_safety_order = True
        self.start_cash            = 0
        self.start_value           = 0
        self.time_period           = None
        self.order      = None
        return

    def get_elapsed_time(self, start_time: float) -> str:
        end_time     = time.time()
        elapsed_time = round(end_time - start_time)
        minutes      = elapsed_time // 60
        seconds      = elapsed_time % 60
        return f"{minutes} minutes {seconds} seconds"

    def money_format(self, money: float) -> str:
        return "${:,.6f}".format(money)

    def print_ohlc(self) -> None:
        open  = self.money_format(self.data.open[0])
        high  = self.money_format(self.data.high[0])
        low   = self.money_format(self.data.low[0])
        close = self.money_format(self.data.close[0])
        print(f"{self.data.datetime.date()} Open: {open}, High: {high}, Low: {low}, Close: {close}")
        return

    def start(self) -> None:
        self.start_cash = self.broker.get_cash()
        return

    def nextstart(self) -> None:
        self.print_ohlc()
        quantity_to_buy = int(self.start_cash / self.data.high[0])
        self.order      = self.buy(size=quantity_to_buy, exectype=bt.Order.Market)
        return

    def next(self) -> None:
        self.print_ohlc()
        return

    def notify_order(self, order: bt.order.BuyOrder) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
            elif order.issell():
                self.log('SELL EXECUTED, Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Canceled]:
            self.log(f'ORDER CANCELED: Size: {order.size}')
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.size, order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED: Size: %.6f Price: %.6f, Cost: %.6f, Comm %.6f' % (order.size, order.price, order.value, order.comm))
        return

    def start(self) -> None:
        self.time_period = self.datas[0].p.todate - self.datas[0].p.fromdate
        self.start_cash  = self.broker.get_cash()
        self.start_value = self.broker.get_value()
        return

    def stop(self) -> None:
        time_elapsed = self.get_elapsed_time(self.start_time)

        total_value  = round(self.broker.get_value()+self.broker.get_cash(), 2)
        profit       = round(total_value - self.start_cash, 2)
        roi          = ((total_value / self.start_cash) - 1.0) * 100
        roi          = '{:.2f}%'.format(roi)

        print("\n\n^^^^ FINISHED BACKTESTING ^^^^^")
        print()
        print(f"Time Elapsed:           {time_elapsed}")
        print(f"Time period:           {self.time_period}")

        print(f"Total Profit:          {self.money_format(profit)}")
        print(f"ROI:                   {roi}")
        print(f"Start Portfolio Value: {self.money_format(self.start_value)}")
        print(f"Final Portfolio Value: {self.money_format(total_value)}")
        return