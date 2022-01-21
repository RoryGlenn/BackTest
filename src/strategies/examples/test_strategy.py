import backtrader
import os
import backtrader
import datetime
import os


STARTING_CASH = 1000000
ORACLE        = "historical_data/oracle.csv"


class TestStrategy(backtrader.Strategy):
    def __init__(self) -> None:
        self.dataclose = self.datas[0].close
        self.order     = None
        self.open_buy_orders = list()
        return

    def log(self, txt: str, dt=None) -> None:
        ''' Logging function fot this strategy'''
        dt = dt or self.data.datetime[0]
        
        if isinstance(dt, float):
            dt = backtrader.num2date(dt)

        _dt = dt.isoformat().split("T")[0]
        print('%s, %s' % (_dt, txt))
        return

    def next(self) -> None:
        self.log('Close %.6f' % self.dataclose[0])

        if self.order:
            # pending order ... do nothing
            return

        if self.position:
            # Check if we are in the market
            # Once we submit our base order and safety orders, there is no more buying or selling left to do until an order is filled
            # print(self.position)
            return

        print(self.position)

        # log the closing price
        # buy_order1 = self.buy(size=1, price=1.0, exectype=backtrader.Order.Limit, auxPrice=1.0)
        buy_order2 = self.buy(size=1, price=2.0, exectype=backtrader.Order.StopLimit)
        
        # self.open_buy_orders.append(buy_order1)
        self.open_buy_orders.append(buy_order2)
        return
    
    def notify_order(self, order: backtrader.order.BuyOrder) -> None:
        if order.status in [order.Submitted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log(txt=f"ORDER SUBMITTED", dt=order.created.dt)
            self.order = order
        elif order.status in [order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log(txt=f"ORDER ACCEPTED", dt=order.created.dt)
            self.order = order
        elif order.status in [order.Expired]:
            self.log('BUY EXPIRED')
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.price, order.executed.value, order.executed.comm))
                self.sell(size=1, price=3.0, exectype=backtrader.Order.Limit)
                self.order = None
            elif order.issell():
                self.log('SELL EXECUTED, Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.price, order.executed.value, order.executed.comm))
                self.order = None
        elif order.status in [order.Canceled]:
            self.log('ORDER CANCELLED, Price: %.6f, Cost: %.6f, Comm %.6f' % (order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Rejected]:
            self.log(f"ORDER WAS REJECTED! {order}")
        
        # Sentinel to None: new orders allowed
        # self.order = None
        return


# createa  bunch of limit orders and try to cancel them
# 

if __name__ == '__main__':
    os.system("cls")

    cerebro = backtrader.Cerebro()
    cerebro.broker.set_cash(STARTING_CASH)

    #BTC-USD
    data = backtrader.feeds.YahooFinanceCSVData(dataname=ORACLE,
                                                fromdate=datetime.datetime(1995, 1, 3),
                                                todate=datetime.datetime(2014, 12, 31))

    cerebro.adddata(data)
    cerebro.addstrategy(TestStrategy)

    starting_value = cerebro.broker.getvalue()
    print(f"Starting Portfolio Value: {starting_value}")
    cerebro.run()

    print()
    profit = round(cerebro.broker.getvalue() - starting_value, 2)
    print(f"Final Portfolio Value: ${round(cerebro.broker.getvalue(), 2)}")
    print(f"Total Profit: ${profit}")
    # cerebro.plot()