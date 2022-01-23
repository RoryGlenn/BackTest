
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
                    safety_order_price_deviation: float, base_order_size: float, 
                    safety_order_size: float) -> None:

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
        self.df_base_order:                     pd.DataFrame  = None
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
        self.base_order_size:              float = base_order_size
        self.safety_order_size:            float = safety_order_size
        return

    def start(self) -> None:
        """
        Sets all values for dollar cost averaging based on the entry price, 
        base order size, safety order size and values from the config file which is set by the user.

        """

        return

    def use_all_cash(self):
        """Spreads out and uses all available cash accross safety orders in order to maximize profit."""
        
        # Use 0.081% of available cash as our base order.

        total_cash      = 1000
        base_order_size = 0.0081 * 1000
        
        """
        instead of calculating safety order 1, 2, ..., n
        start with safety order n, n-1, ... 2, 1.
        
        """


        return

        
