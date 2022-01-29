import backtrader as bt

class Beta(bt.Indicator):
    lines = ("beta"
             , "spread"
             , "spread_sma15"
             , "spread_2sd"
             , "spread_m2sd"
             )

    params = (
        ("period_pct", 1),
        ("period_beta", 15),
    )

    def __init__(self, strat=None):
        """"initialize the line assign it to a variable
        Any operation involving lines objects during __init__ generates another lines object
        Whereas during next it yields regular Python types like floats and bools"""

        self.strategy = strat
        self.line0 = self.strategy.datas[0].close
        self.line1 = self.strategy.datas[1].close

        self.addminperiod(self.params.period_beta + 1)

    def next(self):
        (...)
        #beta
        self.l.beta[0] = model.fit().params

        #spread
        self.l.spread[0] = l0_pct_change[-1] - l1_pct_change[-1] * self.l.beta[0]

        #15 day Spread Moving Average
        datasum = math.fsum(self.l.spread.get(size=self.p.period_beta))
        self.l.spread_sma15[0] = datasum / self.p.period_beta

        #15 Day Standard Deviations
        self.l.spread_2sd[0] = ((((datasum - self.lines.spread_sma[link text](![link url](![image url](image url)))15) ** 2) / self.p.period_beta) ** 0.5) * 2
        self.l.spread_m2sd[0] = ((((datasum - self.lines.spread_sma15) ** 2) / self.p.period_beta) ** 0.5) * -2