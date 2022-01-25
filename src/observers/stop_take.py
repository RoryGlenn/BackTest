# https://community.backtrader.com/topic/163/trailing-stop-loss/10

import backtrader as bt

class SLTPTracking(bt.Observer):

    lines = ('stop', 'take')

    plotinfo = dict(plot=True, subplot=False)

    plotlines = dict(stop=dict(ls=':', linewidth=1.5),
                     take=dict(ls=':', linewidth=1.5))

    def next(self) -> None:
        if self._owner.stop_limit_price != 0.0:
            self.lines.stop[0] = self._owner.stop_limit_price

        if self._owner.take_profit_price != 0.0:
            self.lines.take[0] = self._owner.take_profit_price
        return