from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import os
import pandas     as pd


STARTING_CASH = 1000000
ORACLE        = "historical_data/oracle.csv"
BNGO          = "historical_data/BNGO.csv"


class BuyAndHold(bt.Strategy):
    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def start(self) -> None:
        self.starting_cash = self.broker.get_cash()
        return

    def nextstart(self) -> None:
        quantity_to_buy = int(self.broker.get_cash() / self.data)
        self.buy(size=quantity_to_buy)
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

    def stop(self) -> None:
        profit   = round(self.broker.getvalue() - self.starting_cash, 2)
        self.roi = (self.broker.get_value() / self.starting_cash) - 1.0

        print("\n^^^^ Finished Backtesting ^^^^^")
        print(f"Total Profit: ${profit}")
        print('ROI:        {:.2f}%'.format(100.0 * self.roi))
        print(f"Final Portfolio Value: ${round(self.broker.getvalue(), 2)}")
        return


if __name__ == '__main__':
    os.system("cls")

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(ORACLE)
    df.drop(columns=["Adj Close"], inplace=True)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    data = bt.feeds.PandasData(dataname=df, openinterest=-1)

    cerebro.adddata(data)
    cerebro.addstrategy(BuyAndHold)

    cerebro.run()
    cerebro.plot()        