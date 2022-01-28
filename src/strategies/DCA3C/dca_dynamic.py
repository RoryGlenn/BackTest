
import sys
import pandas as pd

from pprint                       import pprint

# pd.options.display.float_format = '{:,.8f}'.format



class DCADynamic():
    def __init__(self,
                entry_price_usd:                      float, 
                target_profit_percent:                float, 
                safety_orders_max:                    int, 
                safety_orders_active_max:             int, 
                safety_order_volume_scale:            float, 
                safety_order_step_scale:              float, 
                safety_order_price_deviation_percent: float, 
                base_order_size_usd:                  float=0.0,
                base_order_size:                      float=0.0,
                total_usd:                            float=0.0) -> None:

        self.deviation_percent_levels:          list          = [ ]
        self.price_levels:                      list          = [ ]
        
        self.safety_order_quantity_levels:      list          = [ ]
        self.safety_order_quantity_levels_usd:  list          = [ ]
        
        self.total_quantity_levels:             list          = [ ]
        self.total_quantity_levels_usd:         list          = [ ]
        
        self.weighted_average_price_levels:     list          = [ ]
        self.required_price_levels:             list          = [ ]
        self.required_change_percent_levels:    list          = [ ]
        self.profit_levels:                     list          = [ ]
        self.base_order_roi:                    float         = 0.0
        self.safety_order_roi_levels:           list          = [ ]
        self.df:                                pd.DataFrame  = None

        # values to be passed in
        self.entry_price_usd:                      float = entry_price_usd
        self.target_profit_percent:                float = target_profit_percent
        
        self.safety_orders_max:                    int   = safety_orders_max
        self.safety_orders_active_max:             int   = safety_orders_active_max
        self.safety_order_volume_scale:            float = safety_order_volume_scale
        self.safety_order_step_scale:              float = safety_order_step_scale
        self.safety_order_price_deviation_percent: float = safety_order_price_deviation_percent
        self.safety_order_size_usd:                float = 0 # this number will be guessed
        self.base_order_size_usd:                  float = base_order_size_usd
        self.base_order_size:                      float = base_order_size
        self.base_order_cost:                      float = 0.0
        self.base_order_profit:                    float = 0.0
        self.base_order_required_price:            float = 0.0
        self.base_order_deviation_percent:         float = 0.0

        self.total_usd:                            float = total_usd
        self.start()
        return

    def start(self) -> None:
        self.__set_deviation_percent_levels()
        self.__set_price_levels()

        #####################################################################################
        # Start processing data from last safety order to the first safety order.
        #####################################################################################
        # self.__set_quantity_levels_usd()
        # self.__set_total_quantity_levels_usd()
        # self.__get_safety_order_size()
        return

    def __set_deviation_percent_levels(self) -> None:
        price_dev  = self.safety_order_price_deviation_percent
        step_scale = self.safety_order_step_scale
        
        if self.safety_orders_max >= 1:
            # for first safety order
            self.deviation_percent_levels.append(price_dev)

            if self.safety_orders_max >= 2:
                # for second safety order
                step_percent = price_dev * step_scale
                safety_order = price_dev + step_percent
                self.deviation_percent_levels.append(safety_order)
                
                # for 3rd to DCA_.SAFETY_ORDERS_MAX
                for _ in range(2, self.safety_orders_max):
                    step_percent = step_percent * step_scale
                    safety_order = safety_order + step_percent
                    self.deviation_percent_levels.append(safety_order)
        return

    def __set_price_levels(self) -> None:
        for i in range(self.safety_orders_max):
            level = self.deviation_percent_levels[i] / 100
            price = self.entry_price_usd - (self.entry_price_usd * level)
            self.price_levels.append(price)
        return

    def __set_quantity_levels_usd(self) -> None:
        """
        To calculate max_cash to spend on last safety order
        
        start with the total amount we want to spend
            total_usd = 4073

        You can also get the previous total by taking the current steps quantity_usd and substracting it from the total

            previous_total = total_quantity_levels_usd[i] - safety_order_quantity_levels_usd[i]


        If we start at the last safety order, what information do we know?

        We know,
            1. The total amount of USD to spend (Duh..)
            2. The deviation percentage (assuming our safety_order_step_scale doesn't change)
            3. The price
            4. the required price
            5. the total quantity must be less than (total_usd / final_price)

        Is this enough information to figure out the last quantity, quantity_usd, weighted_average_price???
            
            last_quantity_usd = dca.safety_order_volume_scale**(dca.safety_orders_max-1) * dca.safety_order_size
            last_quantity     = last_quantity_usd / price
            



        Calculate the 6th safety order, based on the 7th safety order
            previous_quantity_usd = last_quantity_usd / safety_order_volume_scale



        The question we really want to know is, what is the formula to get from one total volume step to the next? up or down?
            Not sure if this is possible

        Maybe there is an easier way
            -> take the volume scale and the number of safety orders

            # You can figure out safety_order_size if you know the last_quantity_usd
            last_quantity_usd                         = dca.safety_order_volume_scale**(dca.safety_orders_max-1) * dca.safety_order_size           # formula for last_quantity_usd
            last_quantity_usd / dca.safety_order_size = dca.safety_order_volume_scale**(dca.safety_orders_max-1)                                   # divide both sides by safety_order_size
            1 / dca.safety_order_size                 = (dca.safety_order_volume_scale**(dca.safety_orders_max-1)) * (1 / last_quantity_usd)       # multiply both sides by 1/last_quantity_usd
            dca.safety_order_size                     = 1 / ((dca.safety_order_volume_scale**(dca.safety_orders_max-1)) * (1 / last_quantity_usd)) # flip both sides upside down to get final answer


        The total_usd is calculated by doing this
            total_usd = last_quantity_usd + previous_total_usd

        """

        for i in range(self.safety_orders_max-1, -1, -1):
            quantity_usd = (self.safety_order_volume_scale**i) * self.safety_order_size_usd
            self.safety_order_quantity_levels_usd.append(quantity_usd)
        
        self.safety_order_quantity_levels_usd.reverse()
        return

    def __set_total_quantity_levels_usd(self) -> None:
        quantity_usd = self.total_usd

        self.total_quantity_levels_usd.append(quantity_usd)

        # how much more usd do we need to add to self.total_usd to get the 6th safety order quantity_usd accuretly?

        for i in range(self.safety_orders_max-1, -1, -1):
            quantity_usd /= self.safety_order_volume_scale # a little off but it is very close
            self.total_quantity_levels_usd.append(quantity_usd)
        
        self.total_quantity_levels_usd.reverse()
        return

    # def __get_safety_order_size(self) -> None:
    #     for i in range(1, 100):
    #         last_quantity_usd     = self.safety_order_volume_scale**(self.safety_orders_max-1) * i # we will guess the safety order size with i
    #         previous_quantity_usd = last_quantity_usd / self.safety_order_volume_scale
            
    #         if last_quantity_usd > self.total_usd:
    #             print("Could not find the safety order size")
    #             sys.exit()
    #     return





dca = DCADynamic(
            entry_price_usd=36901.57,
            target_profit_percent=1,
            safety_orders_max=7,
            safety_orders_active_max=7,
            safety_order_volume_scale=2.5,
            safety_order_step_scale=1.56,
            safety_order_price_deviation_percent=1.3,
            base_order_size_usd=10,
            total_usd=4000
        )


"""
   safety_order_number  deviation_percent   quantity  total_quantity   quantity_usd  total_quantity_usd           price  weighted_average_price  required_price  required_change_percent       profit  profit_roi_percent
0                    0         0.00000000 0.00027099      0.00027099    10.00000000         10.00000000 36,901.57000000         36,901.57000000 37,270.58570000               1.00000000   0.10000000          1.00000000
1                    1         1.30000000 0.00027456      0.00054555    10.00000000         20.00000000 36,421.84959000         36,660.14050327 37,026.74190830               1.66079517   0.16607952        -83.39204831
2                    2         3.32800000 0.00070080      0.00124635    25.00000000         45.00000000 35,673.48575040         36,105.36295760 36,466.41658718               2.22274561   0.55568640        -44.43135987
3                    3         6.49168000 0.00181128      0.00305763    62.50000000        107.50000000 34,506.03816062         35,157.95562996 35,509.53518626               2.90817804   1.81761128         81.76112775
4                    4        11.42702080 0.00478051      0.00783814   156.25000000        263.75000000 32,684.81992057         33,649.58149519 33,986.07731014               3.98122857   6.22066964        522.06696446
5                    5        19.12615245 0.01308902      0.02092715   390.62500000        654.37500000 29,843.71946609         31,269.18150278 31,581.87331780               5.82418640  22.75072814      2,175.07281422
6                    6        31.13679782 0.03842979      0.05935694   976.56250000      1,630.93750000 25,411.60275711         27,476.77747315 27,751.54524788               9.20816571  89.92349324      8,892.34932362
7                    7        49.87340460 0.13198574      0.19134268 2,441.40625000      4,072.34375000 18,497.50069109         21,282.98701658 21,495.81688675              16.20930441 395.73497100     39,473.49710002

"""
