import pytest

from dca import DCA



entry_price_usd                      = 37153.34
target_profit_percent                = 1.0
safety_orders_max                    = 7
safety_orders_active_max             = 7
safety_order_volume_scale            = 2.5
safety_order_step_scale              = 1.56
safety_order_price_deviation_percent = 1.3
base_order_size_usd                  = 10
safety_order_size_usd                = 10

dca = DCA(
            entry_price_usd=entry_price_usd,
            target_profit_percent=target_profit_percent,
            safety_orders_max=safety_orders_max,
            safety_orders_active_max=safety_orders_active_max,
            safety_order_volume_scale=safety_order_volume_scale,
            safety_order_step_scale=safety_order_step_scale,
            safety_order_price_deviation_percent=safety_order_price_deviation_percent,
            base_order_size_usd=base_order_size_usd,
            safety_order_size_usd=safety_order_size_usd
        )

dca.print_table()



def test_deviation_percent():
    pass
