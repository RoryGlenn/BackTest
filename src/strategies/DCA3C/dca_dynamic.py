
import pandas as pd

DECIMAL_MAX = 8


"""
    CHECK THIS WORKS BY ENTERING IN THE BASE ORDER PRICE AND SAFETY ORDER PRICE WITH THE REGULUAR DCA.
    DOUBLE CHECK BOTH OF THESE BY ENTERING IT INTO 3COMMAS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

"""


class DCADynamic():
    def __init__(self, entry_price: float, target_profit_percent: float, 
                    safety_orders_max: int, safety_orders_active_max: int, 
                    safety_order_volume_scale: float, safety_order_step_scale: float, 
                    safety_order_price_deviation: float, total_cash: float) -> None:

        self.deviation_percent_levels:          list          = [ ]
        self.price_levels:                      list          = [ ]
        self.quantities:                        list          = [ ]
        self.total_quantities:                  list          = [ ]
        self.average_price_levels:              list          = [ ]
        self.required_price_levels:             list          = [ ]
        self.required_change_percent_levels:    list          = [ ]
        self.profit_levels:                     list          = [ ]
        self.cost_levels:                       list          = [ ]
        self.total_cost_levels:                 list          = [ ]
        self.base_order_roi:                    float         = 0.0
        self.safety_order_roi_levels:           list          = [ ]
        # self.df_base_order:                     pd.DataFrame  = None
        self.df_safety_orders:                  pd.DataFrame  = None
        self.df:                                pd.DataFrame  = None

        # values to be passed in
        self.entry_price:                  float = entry_price
        self.target_profit_percent:        float = target_profit_percent
        self.safety_orders_max:            int   = safety_orders_max
        self.safety_orders_active_max:     int   = safety_orders_active_max
        self.safety_order_volume_scale:    float = safety_order_volume_scale
        self.safety_order_step_scale:      float = safety_order_step_scale
        self.safety_order_price_deviation: float = safety_order_price_deviation
        # self.base_order_size:              float = base_order_size
        # self.safety_order_size:            float = safety_order_size
        self.total_cash:                   float = total_cash
        self.start()
        return

    def start(self) -> None:
        """
        Sets all values for dollar cost averaging based on the entry price, 
        base order size, safety order size and values from the config file which is set by the user.

        Spreads out and uses all available cash accross safety orders in order to maximize profit
        
        # Use 0.081% of available cash as our base order.

        total_cash      = 1000
        base_order_size = 0.0081 * 1000
        
        
        instead of calculating safety order 1, 2, ..., n
        start with safety order n, n-1, ... 2, 1.

        """


        self.__set_deviation_percent_levels()
        self.__set_price_levels()
        self.__set_quantity_levels()
        return

    def __set_deviation_percent_levels(self) -> None:
        price_dev  = self.safety_order_price_deviation
        step_scale = self.safety_order_step_scale
        
        if self.safety_orders_max >= 1:
            # for first safety order
            self.deviation_percent_levels.append(round(price_dev, DECIMAL_MAX))

            if self.safety_orders_max >= 2:
                # for second safety order
                step_percent = price_dev * step_scale
                safety_order = price_dev + step_percent
                self.deviation_percent_levels.append(round(safety_order, DECIMAL_MAX))
                
                # for 3rd to DCA_.SAFETY_ORDERS_MAX
                for _ in range(2, self.safety_orders_max):
                    step_percent = step_percent * step_scale
                    safety_order = safety_order + step_percent
                    safety_order = round(safety_order, DECIMAL_MAX)
                    self.deviation_percent_levels.append(safety_order)
        return

    def __set_price_levels(self) -> None:
        for i in range(self.safety_orders_max):
            level = self.deviation_percent_levels[i] / 100
            price = self.entry_price - (self.entry_price * level)
            self.price_levels.append(round(price, DECIMAL_MAX))
        return

    def __set_quantity_levels(self) -> None:
        total_quantity = int(self.total_cash / self.entry_price)
        total_cost     = self.total_cash # roughly...
        total_cash     = self.total_cash

        # for i in range(self.safety_orders_max, 0, -1):
        #     total_cash / step_scale

        """

        How to calculate quantities:
            safety order size
            
        

        safety order step scale * safety order size
        
        
        """
            

        # we want to control the total cost once the final safety order is placed
        # this can be done by changing the safety order size and the base order size at the start ONLY!


        # what is the safety order size used at each level?


        return