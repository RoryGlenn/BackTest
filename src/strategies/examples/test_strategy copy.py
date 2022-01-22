import os
import backtrader as bt
import os
import pandas as pd


STARTING_CASH = 1000000
ORACLE        = "historical_data/oracle.csv"


class TestStrategy(bt.Strategy):
    def __init__(self) -> None:
        self.dataclose = self.datas[0].close
        self.order     = None
        self.open_buy_orders = list()
        return

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        
        if isinstance(dt, float):
            dt = bt.num2date(dt)

        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def next(self) -> None:
        self.log('Close %.6f' % self.dataclose[0])
        # 1995-01-04,2.123457,2.148148,2.092592,2.135803,1.899776,46051600
        
        self.buy(size=3, price=2.092592, exectype=bt.Order.Limit) # LOW   1995-01-04
        self.buy(size=4, price=2.135803, exectype=bt.Order.Limit) # CLOSE 1995-01-04
        self.buy(size=1, price=2.123457, exectype=bt.Order.Limit) # OPEN  1995-01-04
        self.buy(size=2, price=2.148148, exectype=bt.Order.Limit) # HIGH  1995-01-04

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

        return



if __name__ == '__main__':

    # What happens when a user submits 2 orders on the same day? If both are filled, which one gets filled first and why?
    # High/Low execution happens according to the order of submission
    # if High was submitted to the broker first, then it will be executed first
    os.system("cls")

    cerebro = bt.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    df = pd.read_csv(ORACLE)
    df.drop(columns=["Volume", "Adj Close"], inplace=True)
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    df.set_index('Date', inplace=True)

    data = bt.feeds.PandasData(dataname=df, openinterest=-1, volume=-1)

    cerebro.adddata(data)
    cerebro.addstrategy(TestStrategy)

    starting_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: {starting_value}")

    cerebro.run()
    cerebro.plot(volume=False, style='candlestick')