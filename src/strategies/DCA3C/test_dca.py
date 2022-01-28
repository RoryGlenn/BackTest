from dca    import DCA
from pprint import pprint

import pytest


MAX_DECIMAL_PLACES = 8


class DCAScalp7():
    def __init__(self) -> None:
        entry_price_usd                      = 36901.57
        target_profit_percent                = 1.0
        safety_orders_max                    = 7
        safety_orders_active_max             = 7
        safety_order_volume_scale            = 2.5
        safety_order_step_scale              = 1.56
        safety_order_price_deviation_percent = 1.3
        base_order_size_usd                  = 10
        safety_order_size_usd                = 10

        self.dca = DCA(
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

        self.round_everything()
        # self.dca.print_table()
        return

    def round_everything(self) -> None:
        self.dca.base_order_size = round(self.dca.base_order_size, MAX_DECIMAL_PLACES)

        for i in range(self.dca.safety_orders_max):
            self.dca.deviation_percent_levels[i]         = round(self.dca.deviation_percent_levels[i], MAX_DECIMAL_PLACES)
            self.dca.price_levels[i]                     = round(self.dca.price_levels[i], MAX_DECIMAL_PLACES)
            self.dca.safety_order_quantity_levels[i]     = round(self.dca.safety_order_quantity_levels[i], MAX_DECIMAL_PLACES)
            self.dca.safety_order_quantity_levels_usd[i] = round(self.dca.safety_order_quantity_levels_usd[i], MAX_DECIMAL_PLACES)
            self.dca.total_quantity_levels[i]            = round(self.dca.total_quantity_levels[i], MAX_DECIMAL_PLACES)
            self.dca.total_quantity_levels_usd[i]        = round(self.dca.total_quantity_levels_usd[i], MAX_DECIMAL_PLACES)
            self.dca.weighted_average_price_levels[i]    = round(self.dca.weighted_average_price_levels[i], MAX_DECIMAL_PLACES)
            self.dca.required_price_levels[i]            = round(self.dca.required_price_levels[i], MAX_DECIMAL_PLACES)
            self.dca.required_change_percent_levels[i]   = round(self.dca.required_change_percent_levels[i], MAX_DECIMAL_PLACES)
        return


class DCAScalp15():
    def __init__(self) -> None:
        entry_price_usd                      = 2481.92
        target_profit_percent                = 1.0
        safety_orders_max                    = 15
        safety_orders_active_max             = 15
        safety_order_volume_scale            = 1.2
        safety_order_step_scale              = 1.16
        safety_order_price_deviation_percent = 1
        base_order_size                      = 2
        safety_order_size                    = 1

        self.dca = DCA(
                    entry_price_usd=entry_price_usd,
                    target_profit_percent=target_profit_percent,
                    safety_orders_max=safety_orders_max,
                    safety_orders_active_max=safety_orders_active_max,
                    safety_order_volume_scale=safety_order_volume_scale,
                    safety_order_step_scale=safety_order_step_scale,
                    safety_order_price_deviation_percent=safety_order_price_deviation_percent,
                    # base_order_size_usd=base_order_size_usd,
                    # safety_order_size_usd=safety_order_size_usd
                    base_order_size=base_order_size,
                    safety_order_size=safety_order_size
                )

        self.round_everything()
        # self.dca.print_table()
        return

    def round_everything(self) -> None:
        self.dca.base_order_size = round(self.dca.base_order_size, MAX_DECIMAL_PLACES)

        for i in range(self.dca.safety_orders_max):
            self.dca.deviation_percent_levels[i]         = round(self.dca.deviation_percent_levels[i], MAX_DECIMAL_PLACES)
            self.dca.price_levels[i]                     = round(self.dca.price_levels[i], MAX_DECIMAL_PLACES)
            self.dca.safety_order_quantity_levels[i]     = round(self.dca.safety_order_quantity_levels[i], MAX_DECIMAL_PLACES)
            self.dca.safety_order_quantity_levels_usd[i] = round(self.dca.safety_order_quantity_levels_usd[i], MAX_DECIMAL_PLACES)
            self.dca.total_quantity_levels[i]            = round(self.dca.total_quantity_levels[i], MAX_DECIMAL_PLACES)
            self.dca.total_quantity_levels_usd[i]        = round(self.dca.total_quantity_levels_usd[i], MAX_DECIMAL_PLACES)
            self.dca.weighted_average_price_levels[i]    = round(self.dca.weighted_average_price_levels[i], MAX_DECIMAL_PLACES)
            self.dca.required_price_levels[i]            = round(self.dca.required_price_levels[i], MAX_DECIMAL_PLACES)
            self.dca.required_change_percent_levels[i]   = round(self.dca.required_change_percent_levels[i], MAX_DECIMAL_PLACES)
        return



#############################################################################################
### Unit Tests - Scalp7
#############################################################################################

def test_scalp7_deviation_percent() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.base_order_deviation_percent ==  0.00000000
    assert scalp7.dca.deviation_percent_levels[0]  ==  1.30000000
    assert scalp7.dca.deviation_percent_levels[1]  ==  3.32800000
    assert scalp7.dca.deviation_percent_levels[2]  ==  6.49168000
    assert scalp7.dca.deviation_percent_levels[3]  == 11.42702080
    assert scalp7.dca.deviation_percent_levels[4]  == 19.12615245
    assert scalp7.dca.deviation_percent_levels[5]  == 31.13679782
    assert scalp7.dca.deviation_percent_levels[6]  == 49.87340460
    return

def test_scalp7_prices() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.entry_price_usd == 36901.57000000
    assert scalp7.dca.price_levels[0] == 36421.84959000
    assert scalp7.dca.price_levels[1] == 35673.48575040
    assert scalp7.dca.price_levels[2] == 34506.03816062
    assert scalp7.dca.price_levels[3] == 32684.81992057
    assert scalp7.dca.price_levels[4] == 29843.71946609
    assert scalp7.dca.price_levels[5] == 25411.60275711
    assert scalp7.dca.price_levels[6] == 18497.50069109
    return

def test_scalp7_quantity() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.base_order_size                 == 0.00027099
    assert scalp7.dca.safety_order_quantity_levels[0] == 0.00027456
    assert scalp7.dca.safety_order_quantity_levels[1] == 0.00070080
    assert scalp7.dca.safety_order_quantity_levels[2] == 0.00181128
    assert scalp7.dca.safety_order_quantity_levels[3] == 0.00478051
    assert scalp7.dca.safety_order_quantity_levels[4] == 0.01308902
    assert scalp7.dca.safety_order_quantity_levels[5] == 0.03842979
    assert scalp7.dca.safety_order_quantity_levels[6] == 0.13198574
    return

def test_scalp7_quantity_usd() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.base_order_size_usd                 ==   10.00000000
    assert scalp7.dca.safety_order_quantity_levels_usd[0] ==   10.00000000
    assert scalp7.dca.safety_order_quantity_levels_usd[1] ==   25.00000000
    assert scalp7.dca.safety_order_quantity_levels_usd[2] ==   62.50000000
    assert scalp7.dca.safety_order_quantity_levels_usd[3] ==  156.25000000
    assert scalp7.dca.safety_order_quantity_levels_usd[4] ==  390.62500000
    assert scalp7.dca.safety_order_quantity_levels_usd[5] ==  976.56250000
    assert scalp7.dca.safety_order_quantity_levels_usd[6] == 2441.40625000
    return

def test_scalp7_total_quantity() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.base_order_size          == 0.00027099
    assert scalp7.dca.total_quantity_levels[0] == 0.00054555
    assert scalp7.dca.total_quantity_levels[1] == 0.00124635
    assert scalp7.dca.total_quantity_levels[2] == 0.00305763
    assert scalp7.dca.total_quantity_levels[3] == 0.00783814
    assert scalp7.dca.total_quantity_levels[4] == 0.02092715
    assert scalp7.dca.total_quantity_levels[5] == 0.05935694
    assert scalp7.dca.total_quantity_levels[6] == 0.19134268
    return

def test_scalp7_total_quantity_usd() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.base_order_size_usd          ==   10.00000000
    assert scalp7.dca.total_quantity_levels_usd[0] ==   20.00000000
    assert scalp7.dca.total_quantity_levels_usd[1] ==   45.00000000
    assert scalp7.dca.total_quantity_levels_usd[2] ==  107.50000000
    assert scalp7.dca.total_quantity_levels_usd[3] ==  263.75000000
    assert scalp7.dca.total_quantity_levels_usd[4] ==  654.37500000
    assert scalp7.dca.total_quantity_levels_usd[5] == 1630.93750000
    assert scalp7.dca.total_quantity_levels_usd[6] == 4072.34375000
    return

def test_scalp7_weighted_average_price() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.entry_price_usd                  == 36901.57000000
    assert scalp7.dca.weighted_average_price_levels[0] == 36660.14050327
    assert scalp7.dca.weighted_average_price_levels[1] == 36105.36295760
    assert scalp7.dca.weighted_average_price_levels[2] == 35157.95562996
    assert scalp7.dca.weighted_average_price_levels[3] == 33649.58149519
    assert scalp7.dca.weighted_average_price_levels[4] == 31269.18150278
    assert scalp7.dca.weighted_average_price_levels[5] == 27476.77747315
    assert scalp7.dca.weighted_average_price_levels[6] == 21282.98701658
    return

def test_scalp7_required_price() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.base_order_required_price == 37270.58570000
    assert scalp7.dca.required_price_levels[0]  == 37026.74190830
    assert scalp7.dca.required_price_levels[1]  == 36466.41658718
    assert scalp7.dca.required_price_levels[2]  == 35509.53518626
    assert scalp7.dca.required_price_levels[3]  == 33986.07731014
    assert scalp7.dca.required_price_levels[4]  == 31581.87331780
    assert scalp7.dca.required_price_levels[5]  == 27751.54524788
    assert scalp7.dca.required_price_levels[6]  == 21495.81688675
    return

def test_scalp7_required_change_percent() -> None:
    scalp7 = DCAScalp7()
    assert scalp7.dca.target_profit_percent             ==  1.00000000
    assert scalp7.dca.required_change_percent_levels[0] ==  1.66079517
    assert scalp7.dca.required_change_percent_levels[1] ==  2.22274561
    assert scalp7.dca.required_change_percent_levels[2] ==  2.90817804
    assert scalp7.dca.required_change_percent_levels[3] ==  3.98122857
    assert scalp7.dca.required_change_percent_levels[4] ==  5.82418640
    assert scalp7.dca.required_change_percent_levels[5] ==  9.20816571
    assert scalp7.dca.required_change_percent_levels[6] == 16.20930441
    return



#############################################################################################
### Unit Tests - Scalp15
#############################################################################################

def test_scalp15_deviation_percent() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.base_order_deviation_percent  ==  0.00000000
    assert scalp15.dca.deviation_percent_levels[0]   ==  1.00000000
    assert scalp15.dca.deviation_percent_levels[1]   ==  2.16000000
    assert scalp15.dca.deviation_percent_levels[2]   ==  3.50560000
    assert scalp15.dca.deviation_percent_levels[3]   ==  5.06649600
    assert scalp15.dca.deviation_percent_levels[4]   ==  6.87713536
    assert scalp15.dca.deviation_percent_levels[5]   ==  8.97747702
    assert scalp15.dca.deviation_percent_levels[6]   == 11.41387334
    assert scalp15.dca.deviation_percent_levels[7]   == 14.24009307
    assert scalp15.dca.deviation_percent_levels[8]   == 17.51850797
    assert scalp15.dca.deviation_percent_levels[9]   == 21.32146924
    assert scalp15.dca.deviation_percent_levels[10]  == 25.73290432
    assert scalp15.dca.deviation_percent_levels[11]  == 30.85016901
    assert scalp15.dca.deviation_percent_levels[12]  == 36.78619605
    assert scalp15.dca.deviation_percent_levels[13]  == 43.67198742
    assert scalp15.dca.deviation_percent_levels[14]  == 51.65950541
    return

def test_scalp15_prices() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.entry_price_usd  == 2481.92000000
    assert scalp15.dca.price_levels[0]  == 2457.10080000
    assert scalp15.dca.price_levels[1]  == 2428.31052800
    assert scalp15.dca.price_levels[2]  == 2394.91381248
    assert scalp15.dca.price_levels[3]  == 2356.17362248
    assert scalp15.dca.price_levels[4]  == 2311.23500207
    assert scalp15.dca.price_levels[5]  == 2259.10620240
    assert scalp15.dca.price_levels[6]  == 2198.63679479
    assert scalp15.dca.price_levels[7]  == 2128.49228196
    assert scalp15.dca.price_levels[8]  == 2047.12464707
    assert scalp15.dca.price_levels[9]  == 1952.73819060
    assert scalp15.dca.price_levels[10] == 1843.24990110
    assert scalp15.dca.price_levels[11] == 1716.24348527
    assert scalp15.dca.price_levels[12] == 1568.91604291
    assert scalp15.dca.price_levels[13] == 1398.01620978
    assert scalp15.dca.price_levels[14] == 1199.77240335
    return

def test_scalp15_quantity() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.base_order_size                  ==  2.00000000
    assert scalp15.dca.safety_order_quantity_levels[0]  ==  1.00000000
    assert scalp15.dca.safety_order_quantity_levels[1]  ==  1.20000000
    assert scalp15.dca.safety_order_quantity_levels[2]  ==  1.44000000
    assert scalp15.dca.safety_order_quantity_levels[3]  ==  1.72800000
    assert scalp15.dca.safety_order_quantity_levels[4]  ==  2.07360000
    assert scalp15.dca.safety_order_quantity_levels[5]  ==  2.48832000
    assert scalp15.dca.safety_order_quantity_levels[6]  ==  2.98598400
    assert scalp15.dca.safety_order_quantity_levels[7]  ==  3.58318080
    assert scalp15.dca.safety_order_quantity_levels[8]  ==  4.29981696
    assert scalp15.dca.safety_order_quantity_levels[9]  ==  5.15978035
    assert scalp15.dca.safety_order_quantity_levels[10] ==  6.19173642
    assert scalp15.dca.safety_order_quantity_levels[11] ==  7.43008371
    assert scalp15.dca.safety_order_quantity_levels[12] ==  8.91610045
    assert scalp15.dca.safety_order_quantity_levels[13] == 10.69932054
    assert scalp15.dca.safety_order_quantity_levels[14] == 12.83918465
    return

def test_scalp15_quantity_usd() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.base_order_cost                      ==  4963.84000000
    assert scalp15.dca.safety_order_quantity_levels_usd[0]  ==  2457.10080000
    assert scalp15.dca.safety_order_quantity_levels_usd[1]  ==  2913.97263360
    assert scalp15.dca.safety_order_quantity_levels_usd[2]  ==  3448.67588997
    assert scalp15.dca.safety_order_quantity_levels_usd[3]  ==  4071.46801964
    assert scalp15.dca.safety_order_quantity_levels_usd[4]  ==  4792.57690030
    assert scalp15.dca.safety_order_quantity_levels_usd[5]  ==  5621.37914557
    assert scalp15.dca.safety_order_quantity_levels_usd[6]  ==  6565.09429105
    assert scalp15.dca.safety_order_quantity_levels_usd[7]  ==  7626.77267765
    assert scalp15.dca.safety_order_quantity_levels_usd[8]  ==  8802.26127670
    assert scalp15.dca.safety_order_quantity_levels_usd[9]  == 10075.70014846
    assert scalp15.dca.safety_order_quantity_levels_usd[10] == 11412.91754820
    assert scalp15.dca.safety_order_quantity_levels_usd[11] == 12751.83275695
    assert scalp15.dca.safety_order_quantity_levels_usd[12] == 13988.61303351
    assert scalp15.dca.safety_order_quantity_levels_usd[13] == 14957.82354564
    assert scalp15.dca.safety_order_quantity_levels_usd[14] == 15404.09941912
    return

def test_scalp15_total_quantity() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.base_order_size           ==  2.00000000
    assert scalp15.dca.total_quantity_levels[0]  ==  3.00000000
    assert scalp15.dca.total_quantity_levels[1]  ==  4.20000000
    assert scalp15.dca.total_quantity_levels[2]  ==  5.64000000
    assert scalp15.dca.total_quantity_levels[3]  ==  7.36800000
    assert scalp15.dca.total_quantity_levels[4]  ==  9.44160000
    assert scalp15.dca.total_quantity_levels[5]  == 11.92992000
    assert scalp15.dca.total_quantity_levels[6]  == 14.91590400
    assert scalp15.dca.total_quantity_levels[7]  == 18.49908480
    assert scalp15.dca.total_quantity_levels[8]  == 22.79890176
    assert scalp15.dca.total_quantity_levels[9]  == 27.95868211
    assert scalp15.dca.total_quantity_levels[10] == 34.15041853
    assert scalp15.dca.total_quantity_levels[11] == 41.58050224
    assert scalp15.dca.total_quantity_levels[12] == 50.49660269
    assert scalp15.dca.total_quantity_levels[13] == 61.19592323
    assert scalp15.dca.total_quantity_levels[14] == 74.03510787
    return

def test_scalp15_total_quantity_usd() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.base_order_size_usd           ==   4963.84000000
    assert scalp15.dca.total_quantity_levels_usd[0]  ==   7420.94080000
    assert scalp15.dca.total_quantity_levels_usd[1]  ==  10334.91343360
    assert scalp15.dca.total_quantity_levels_usd[2]  ==  13783.58932357
    assert scalp15.dca.total_quantity_levels_usd[3]  ==  17855.05734321
    assert scalp15.dca.total_quantity_levels_usd[4]  ==  22647.63424351
    assert scalp15.dca.total_quantity_levels_usd[5]  ==  28269.01338908
    assert scalp15.dca.total_quantity_levels_usd[6]  ==  34834.10768013
    assert scalp15.dca.total_quantity_levels_usd[7]  ==  42460.88035778
    assert scalp15.dca.total_quantity_levels_usd[8]  ==  51263.14163448
    assert scalp15.dca.total_quantity_levels_usd[9]  ==  61338.84178294
    assert scalp15.dca.total_quantity_levels_usd[10] ==  72751.75933114
    assert scalp15.dca.total_quantity_levels_usd[11] ==  85503.59208809
    assert scalp15.dca.total_quantity_levels_usd[12] ==  99492.20512160
    assert scalp15.dca.total_quantity_levels_usd[13] == 114450.02866723
    assert scalp15.dca.total_quantity_levels_usd[14] == 129854.12808635
    return

def test_scalp15_weighted_average_price() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.entry_price_usd                   == 2481.92000000
    assert scalp15.dca.weighted_average_price_levels[0]  == 2473.64693333
    assert scalp15.dca.weighted_average_price_levels[1]  == 2460.69367467
    assert scalp15.dca.weighted_average_price_levels[2]  == 2443.89881624
    assert scalp15.dca.weighted_average_price_levels[3]  == 2423.32482943
    assert scalp15.dca.weighted_average_price_levels[4]  == 2398.70723643
    assert scalp15.dca.weighted_average_price_levels[5]  == 2369.58951854
    assert scalp15.dca.weighted_average_price_levels[6]  == 2335.36684603
    assert scalp15.dca.weighted_average_price_levels[7]  == 2295.29627097
    assert scalp15.dca.weighted_average_price_levels[8]  == 2248.49171132
    assert scalp15.dca.weighted_average_price_levels[9]  == 2193.91034017
    assert scalp15.dca.weighted_average_price_levels[10] == 2130.33287595
    assert scalp15.dca.weighted_average_price_levels[11] == 2056.33860774
    assert scalp15.dca.weighted_average_price_levels[12] == 1970.27522294
    assert scalp15.dca.weighted_average_price_levels[13] == 1870.22309055
    assert scalp15.dca.weighted_average_price_levels[14] == 1753.95338532
    return

def test_scalp15_required_price() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.base_order_required_price == 2506.73920000
    assert scalp15.dca.required_price_levels[0]  == 2498.38340267
    assert scalp15.dca.required_price_levels[1]  == 2485.30061141
    assert scalp15.dca.required_price_levels[2]  == 2468.33780440
    assert scalp15.dca.required_price_levels[3]  == 2447.55807772
    assert scalp15.dca.required_price_levels[4]  == 2422.69430880
    assert scalp15.dca.required_price_levels[5]  == 2393.28541373
    assert scalp15.dca.required_price_levels[6]  == 2358.72051449
    assert scalp15.dca.required_price_levels[7]  == 2318.24923368
    assert scalp15.dca.required_price_levels[8]  == 2270.97662843
    assert scalp15.dca.required_price_levels[9]  == 2215.84944357
    assert scalp15.dca.required_price_levels[10] == 2151.63620471
    assert scalp15.dca.required_price_levels[11] == 2076.90199382
    assert scalp15.dca.required_price_levels[12] == 1989.97797516
    assert scalp15.dca.required_price_levels[13] == 1888.92532145
    assert scalp15.dca.required_price_levels[14] == 1771.49291917
    return

def test_scalp15_required_change_percent() -> None:
    scalp15 = DCAScalp15()
    assert scalp15.dca.target_profit_percent              ==  1.00000000
    assert scalp15.dca.required_change_percent_levels[0]  ==  1.68013468
    assert scalp15.dca.required_change_percent_levels[1]  ==  2.34690262
    assert scalp15.dca.required_change_percent_levels[2]  ==  3.06583024
    assert scalp15.dca.required_change_percent_levels[3]  ==  3.87851109
    assert scalp15.dca.required_change_percent_levels[4]  ==  4.82249995
    assert scalp15.dca.required_change_percent_levels[5]  ==  5.93948222
    assert scalp15.dca.required_change_percent_levels[6]  ==  7.28104433
    assert scalp15.dca.required_change_percent_levels[7]  ==  8.91508761
    assert scalp15.dca.required_change_percent_levels[8]  == 10.93494632
    assert scalp15.dca.required_change_percent_levels[9]  == 13.47396462
    assert scalp15.dca.required_change_percent_levels[10] == 16.73057481
    assert scalp15.dca.required_change_percent_levels[11] == 21.01441384
    assert scalp15.dca.required_change_percent_levels[12] == 26.83776064
    assert scalp15.dca.required_change_percent_levels[13] == 35.11469382
    assert scalp15.dca.required_change_percent_levels[14] == 47.65241426
    return
