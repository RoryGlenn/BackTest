"""dca.py - DCA is a dollar cost averaging technique. 
This bot uses DCA in order lower the average buy price for a purchased coin."""

import sys
import pandas as pd

from pprint                       import pprint

pd.options.display.float_format = '{:,.8f}'.format


# why don't we just set base_order_quantity or base_order_quantity_usd right
#  in the beginning instead of doing all of these checks??????????????????????????????????????????


class DCA():
    def __init__(self,
                entry_price_usd:                      float, 
                target_profit_percent:                float, 
                safety_orders_max:                    int, 
                safety_orders_active_max:             int, 
                safety_order_volume_scale:            float, 
                safety_order_step_scale:              float, 
                safety_order_price_deviation_percent: float, 
                base_order_size_usd:                  float=0.0,
                safety_order_size_usd:                float=0.0,
                base_order_size:                      float=0.0,
                safety_order_size:                    float=0.0,
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
        self.safety_order_size:                    float = safety_order_size
        self.safety_order_size_usd:                float = safety_order_size_usd        
        
        self.base_order_size_usd:                  float = base_order_size_usd
        self.base_order_size:                      float = base_order_size
        self.base_order_cost:                      float = 0.0
        self.base_order_profit:                    float = 0.0
        self.base_order_required_price:            float = 0.0
        self.base_order_deviation_percent:         float = 0.0

        self.total_usd:                            float = total_usd

        if self.total_usd > 0:
            """spreads out and uses all available cash accross safety orders in order to maximize profit."""
            # self.start()
            self.optimize()
        else:
            self.start()
        return

    def start(self) -> None:
        """
        Sets all values for dollar cost averaging based on the entry price, 
        base order size, safety order size and values from the config file which is set by the user.

        """

        self.__set_base_order_variables()
        self.__set_deviation_percent_levels()
        self.__set_price_levels()

        if self.base_order_size > 0 and self.safety_order_size > 0 and \
            self.base_order_size_usd == 0 and self.safety_order_size_usd == 0:
            # quantity of coin to buy determines usd spent
            self.__set_quantity_levels()
            self.__set_quantity_usd_levels_dependent()
        elif self.base_order_size_usd > 0 and self.safety_order_size_usd > 0 and \
            self.base_order_size == 0 and self.safety_order_size == 0:
            # usd spent determines quantity to buy
            self.__set_quantity_usd_levels()
            self.__set_quantity_levels_dependent()
        else:
            print("Invalid sizes for base order and/or safety order")
            sys.exit()

        self.__set_total_quantity_levels()
        self.__set_total_quantity_usd_levels()
        
        self.__set_weighted_average_price_levels()
        self.__set_required_price_levels()
        self.__set_required_change_percentage_levels()
        self.__set_profit_levels()
        self.__set_base_order_roi_level()
        self.__set_safety_order_roi_levels()
        self.__set_df_table()
        return

    def __set_base_order_variables(self) -> None:
        self.base_order_required_price = self.entry_price_usd + ( self.entry_price_usd * (self.target_profit_percent/100) )

        if self.base_order_size > 0 and self.safety_order_size > 0 and \
            self.base_order_size_usd == 0 and self.safety_order_size_usd == 0:
            # quantity of coin to buy determines usd spent
            self.base_order_cost   = self.entry_price_usd * self.base_order_size
            self.base_order_profit = (self.base_order_required_price - self.entry_price_usd) * self.base_order_size            
        elif self.base_order_size_usd > 0 and self.safety_order_size_usd > 0 and \
            self.base_order_size == 0 and self.safety_order_size == 0:
            # usd spent determines quantity to buy
            self.base_order_cost      = self.base_order_size_usd
            base_order_size           = self.base_order_size_usd / self.entry_price_usd
            self.base_order_profit    = (self.base_order_required_price - self.entry_price_usd) * base_order_size
        return

    def __set_deviation_percent_levels(self) -> None:
        """
        Deviation percent levels:

        The safety order step scale will multiply each step by a given number.
        
        Example:
            Let's assume there is a coin that is originally bought at a price of $100.0 and the current bot is set to
            purchase the same coin with a safety order price deviation of 1% from the original price with a safety order step scale of 2.
            
            This is how we calculate the safety order prices:
                Step 0: It's the first order, we use the base order deviation to place it: 0% + -1% = -1%, 
                where base_order_price_deviation = 0% and safety_order_price_deviation is 1%.
                (The base order deviation is 0% because in order to start a trade, there must be no deviation)

                Last safety order step is multiplied by the scale and then added to the last order percentage. 
                The last step was 1%, the new step will be 1% * 2 = 2%. The order will be placed: -1% + -2% = -3%.

                Step 0: ...           Order 1: 0%  + 1%  = 1%   (1st and only base_order_price_deviation)
                Step 1: 1% * 2 = 2%.  Order 2: 1%  + 2%  = 3%.  (1st safety_order_price_deviation)
                Step 2: 2% * 2 = 4%.  Order 3: 3%  + 4%  = 7%.  (2nd safety_order_price_deviation)
                Step 3: 4% * 2 = 8%.  Order 4: 7%  + 8%  = 15%. (3rd safety_order_price_deviation)
                Step 4: 8% * 2 = 16%. Order 5: 15% + 16% = 31%. (4th safety_order_price_deviation)
                .
                .
                .
                Step n: n% * 2 = (2*n)%. Order n: ((2 * n) - 1)% + (2*n)% = (2n-1)% + (2n)%. (nth safety_order_price_deviation)
                    (side node: Please double check correctness of the line above as I'm not 100% sure it is accurate)

        For more info: https://help.3commas.io/en/articles/3108940-main-settings
        """

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
        """Save the coin prices levels in terms of USD into self.price_levels.
        Order 0: $34.4317911
        Order 1: $33.72431722
        Order n: ..."""

        # safety orders
        for i in range(self.safety_orders_max):
            level = self.deviation_percent_levels[i] / 100
            price = self.entry_price_usd - (self.entry_price_usd * level)
            self.price_levels.append(price)
        return

    def __set_quantity_levels(self) -> None:
        """Sets the quantity to buy for each safety order number."""

        prev_so_quantity = self.safety_order_size_usd / self.entry_price_usd if self.safety_order_size == 0 else self.safety_order_size

        # first safety order
        self.safety_order_quantity_levels.append(prev_so_quantity)

        # remaining safety orders
        for _ in range(1, self.safety_orders_max):
            so_quantity = self.safety_order_volume_scale * prev_so_quantity
            self.safety_order_quantity_levels.append(so_quantity)
            prev_so_quantity = so_quantity
        return

    def __set_quantity_levels_dependent(self) -> None:
        """
        WARNING: 
            This function should only be called when the user wants to make trades based on USD rather than coin quantity
            Because of this, it is dependent on __set_quantity_usd_levels()
        
            In other words, the amount of money to spend is determined by the base_order_size_usd and 
            safety_order_size_usd variables and cannot be calculated indepentendly of them!

            Call these two functions like so:
                self.__set_quantity_usd_levels()
                self.__set_quantity_levels_dependent()

        """

        for i in range(self.safety_orders_max):
            quantity = self.safety_order_quantity_levels_usd[i] / self.price_levels[i]
            self.safety_order_quantity_levels.append(quantity)
        return

    def __set_quantity_usd_levels_dependent(self) -> None:
        """
        WARNING: 
            This function should only be called when the user wants to make trades based on coin quantity rather than USD
            Because of this, it is dependent on __set_quantity_levels()
        
            In other words, the amount of money to spend is determined by the base_order_size and safety_order_size variables
            and cannot be calculated indepentendly of them!

            Call these two functions like so:
                self.__set_quantity_levels()
                self.__set_quantity_usd_levels_dependent()

        """
        for i in range(self.safety_orders_max):
            usd_quantity = self.price_levels[i] * self.safety_order_quantity_levels[i]
            self.safety_order_quantity_levels_usd.append(usd_quantity)
        return

    def __set_quantity_usd_levels(self) -> None:
        prev_so_usd_quantity = self.safety_order_size * self.entry_price_usd if self.safety_order_size_usd == 0 else self.safety_order_size_usd
        
        # first safety order
        self.safety_order_quantity_levels_usd.append(prev_so_usd_quantity)

        # remaining safety orders
        for _ in range(1, self.safety_orders_max):
            so_quantity = self.safety_order_volume_scale * prev_so_usd_quantity
            self.safety_order_quantity_levels_usd.append(so_quantity)
            prev_so_usd_quantity = so_quantity
        return

    def __set_total_quantity_levels(self) -> None:
        """Sets the total quantity bought at each level."""
        prev = self.base_order_cost / self.entry_price_usd if self.base_order_size == 0 else self.base_order_size
        
        for i in range(self.safety_orders_max):
            sum = prev + self.safety_order_quantity_levels[i]
            self.total_quantity_levels.append(sum)
            prev = sum 
        return

    def __set_total_quantity_usd_levels(self) -> None:
        """Sets the total quantity bought at each level."""
        prev = self.base_order_cost if self.base_order_size_usd == 0 else self.base_order_size_usd
        
        for i in range(self.safety_orders_max):
            sum = prev + self.safety_order_quantity_levels_usd[i]
            self.total_quantity_levels_usd.append(sum)
            prev = sum
        return
    
    def __set_weighted_average_price_levels(self) -> None:
        """Sets the weighted average price level for each safety order number."""
        base_order_qty = self.base_order_cost / self.entry_price_usd if self.base_order_size_usd == 0 else self.base_order_size_usd / self.entry_price_usd
        
        for i in range(self.safety_orders_max):
            numerator = self.entry_price_usd * base_order_qty

            for j in range(i+1):
                numerator += self.price_levels[j] * self.safety_order_quantity_levels[j]
                
            weighted_average = numerator / self.total_quantity_levels[i]
            self.weighted_average_price_levels.append(weighted_average)
        return
    
    def __set_required_price_levels(self) -> None:
        """Sets the required price for each safety order number."""
        target_profit_decimal = self.target_profit_percent / 100

        # safety orders
        for i in range(self.safety_orders_max):
            required_price = self.weighted_average_price_levels[i] + (self.weighted_average_price_levels[i] * target_profit_decimal)
            self.required_price_levels.append(required_price)
        return

    def __set_required_change_percentage_levels(self) -> None:
        """Sets the required change percent for each safety order number."""
        for i in range(self.safety_orders_max):
            required_change_percentage = ((self.required_price_levels[i] / self.price_levels[i]) - 1) * 100
            self.required_change_percent_levels.append(required_change_percentage)
        return
    
    def __set_profit_levels(self) -> None:
        """The more safety orders that are filled, the larger the profit will be.
        Each profit level is based on the previous profit level except for the base order."""
        
        for i in range(self.safety_orders_max):
            so_entry_value = self.price_levels[i] * self.safety_order_quantity_levels[i]
            so_exit_value  = self.required_price_levels[i] * self.safety_order_quantity_levels[i]
            profit         = so_exit_value - so_entry_value 
            self.profit_levels.append(profit)
        return

    def __set_base_order_roi_level(self) -> None:
        if self.base_order_size_usd == 0:
            base_order_size_usd    = self.entry_price_usd * self.base_order_size
            base_order_entry_value = base_order_size_usd * self.entry_price_usd
            base_order_exit_value  = base_order_size_usd * ( self.entry_price_usd + (self.entry_price_usd * (self.target_profit_percent/100)) )
        else:
            base_order_entry_value = self.base_order_size_usd * self.entry_price_usd
            base_order_exit_value  = self.base_order_size_usd * ( self.entry_price_usd + (self.entry_price_usd * (self.target_profit_percent/100)) )

        base_order_roi = (base_order_exit_value / base_order_entry_value) - 1.0
        base_order_roi *= 100 # convert to percentage
        return

    def __set_safety_order_roi_levels(self) -> None:
        """
        ROI levels is calculated in relation to the base order profit.

            1. Suppose a base order is placed and sold for a profit (no safety orders were filled).
                base entry price  = $1.00
                take profit price = $1.01
                profit            = $0.01

                roi is 1%
            
            2. Now suppose that a base order was placed and safety order number 1 was placed.
            Both orders are filled along with our take profit order.
                base entry price           = $1.00
                safety order 1 entry price = $0.987
                take profit price          = $1.005623
                profit                     = $0.014805

                roi is 48% higher than our base order profit

            In conclusion:
                for each safety order that is filled, the roi increases along with our cash profit in relationship to the base order roi. 
        
            Side note:
                We can also calculate the ROI according to the total cost, however this information is not useful because 
                this number is always 1%.

        """

        for i in range(self.safety_orders_max):
            profit_roi = (self.profit_levels[i] / self.target_profit_percent) - 1
            profit_roi *= 100
            self.safety_order_roi_levels.append(profit_roi)
        return

    def __set_df_table(self) -> None:
        safety_order_numbers = [i for i in range(self.safety_orders_max+1)]
        self.base_order_size = self.base_order_size_usd / self.entry_price_usd if self.base_order_size == 0 else self.base_order_size
        self.base_order_size_usd = self.base_order_cost

        self.df = pd.DataFrame(
            {
                'safety_order_number':     safety_order_numbers,
                'deviation_percent':       [0]                               + self.deviation_percent_levels,
                'quantity':                [self.base_order_size]                 + self.safety_order_quantity_levels,
                'total_quantity':          [self.base_order_size]                 + self.total_quantity_levels,
                'quantity_usd':            [self.base_order_cost]            + self.safety_order_quantity_levels_usd,
                'total_quantity_usd':      [self.base_order_cost]            + self.total_quantity_levels_usd,
                'price':                   [self.entry_price_usd]            + self.price_levels,
                'weighted_average_price':  [self.entry_price_usd]            + self.weighted_average_price_levels,
                'required_price':          [self.base_order_required_price]  + self.required_price_levels,
                'required_change_percent': [self.target_profit_percent]      + self.required_change_percent_levels,
                'profit':                  [self.base_order_profit]          + self.profit_levels,
                'profit_roi_percent':      [self.target_profit_percent]      + self.safety_order_roi_levels
            })
            
        return
    
    def remove_top_safety_order(self) -> None:
        self.deviation_percent_levels.pop(0)
        self.safety_order_quantity_levels.pop(0)
        self.total_quantity_levels.pop(0)
        self.safety_order_quantity_levels_usd.pop(0)
        self.total_quantity_levels_usd.pop(0)
        self.price_levels.pop(0)
        self.weighted_average_price_levels.pop(0)
        self.required_price_levels.pop(0)
        self.required_change_percent_levels.pop(0)
        self.profit_levels.pop(0)
        self.safety_order_roi_levels.pop(0)
        return
    
    def reset(self) -> None:
        self.deviation_percent_levels = []
        self.safety_order_quantity_levels = []
        self.total_quantity_levels = []
        self.safety_order_quantity_levels_usd = []
        self.total_quantity_levels_usd = []
        self.price_levels = []
        self.weighted_average_price_levels = []
        self.required_price_levels = []
        self.required_change_percent_levels = []
        self.profit_levels = []
        self.safety_order_roi_levels = []
        return

    def print_table(self) -> None:
        print(self.df)
        return


    def optimize(self) -> None:
        # if the last safety order uses all of our cash within a 1% deviation
        upper_limit                = self.total_usd
        self.base_order_size_usd   = self.base_order_size   * self.entry_price_usd
        self.safety_order_size_usd = self.safety_order_size * self.entry_price_usd

        upper = False
        lower = False

        ### DYNAMIC DCA ##
        while True:
            self.base_order_size   = 0
            self.safety_order_size = 0
            self.start()

            if upper and lower:
                # self.safety_order_size_usd -= 1
                break

            if self.total_quantity_levels_usd[-1] > upper_limit: # maybe this need to be within 1% of total_usd rather than 1 dollar
                self.safety_order_size_usd -= 1
                upper = True
            else:
                self.safety_order_size_usd += 1
                lower = True
            
            self.reset()

        if self.total_quantity_levels_usd[-1] >= self.total_usd:
            # this should never happen!!!
            print("last safety order is greater than all our cash!")
            print(self.total_quantity_levels_usd)

        self.base_order_size_usd = self.safety_order_size_usd * 2
        return



# dca = DCA(
#             entry_price_usd=10,
#             target_profit_percent=1,
#             safety_orders_max=7,
#             safety_orders_active_max=7,
#             safety_order_volume_scale=2.5,
#             safety_order_step_scale=1,
#             safety_order_price_deviation_percent=3,
#             base_order_size_usd=10,
#             safety_order_size_usd=10
#         )

# dca.print_table()