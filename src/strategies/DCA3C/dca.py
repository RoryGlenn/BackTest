"""dca.py - DCA is a dollar cost averaging technique. 
This bot uses DCA in order lower the average buy price for a purchased coin."""

import pandas as pd

DECIMAL_MAX = 8


class DCA():
    def __init__(self, entry_price: float, target_profit_percent: float, safety_orders_max: int,
                        safety_orders_active_max: int, safety_order_volume_scale: float, safety_order_step_scale: float, 
                        safety_order_price_deviation: float, base_order_size: float, safety_order_size: float):
                        
        self.deviation_percentage_levels:       list          = [ ]
        self.price_levels:                      list          = [ ]
        self.quantities:                        list          = [ ]
        self.total_quantities:                  list          = [ ]
        self.average_price_levels:              list          = [ ]
        self.required_price_levels:             list          = [ ]
        self.required_change_percentage_levels: list          = [ ]
        self.profit_levels:                     list          = [ ]
        self.cost_levels:                       list          = [ ]
        self.total_cost_levels:                 list          = [ ]
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
        self.__set_deviation_percentage_levels()
        self.__set_price_levels()
        self.__set_quantity_levels()
        self.__set_total_quantity_levels()
        self.__set_weighted_average_price_levels()
        self.__set_required_price_levels()
        self.__set_required_change_percentage_levels()
        self.__set_profit_levels()
        self.__set_cost_levels()
        self.__set_total_cost_levels()
        return

    def __set_deviation_percentage_levels(self) -> None:
        """
        Safety order step scale:

        The safety order step scale will multiply each step in by a certain percent.
        
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

        price_dev  = self.safety_order_price_deviation
        step_scale = self.safety_order_step_scale
        
        # for first safety order
        self.deviation_percentage_levels.append(round(price_dev, DECIMAL_MAX))

        # for second safety order
        step_percent = price_dev * step_scale
        safety_order = price_dev + step_percent
        self.deviation_percentage_levels.append(round(safety_order, DECIMAL_MAX))
        
        # for 3rd to DCA_.SAFETY_ORDERS_MAX
        for _ in range(2, self.safety_orders_max):
            step_percent = step_percent * step_scale
            safety_order = safety_order + step_percent
            safety_order = round(safety_order, DECIMAL_MAX)
            self.deviation_percentage_levels.append(safety_order)
        return

    def __set_price_levels(self) -> None:
        """Save the coin prices levels in terms of USD into self.price_levels.
        Order 0: $34.4317911
        Order 1: $33.72431722
        Order n: ..."""

        # safety orders
        for i in range(self.safety_orders_max):
            level = self.deviation_percentage_levels[i] / 100
            price = self.entry_price - (self.entry_price * level)
            self.price_levels.append(round(price, DECIMAL_MAX))
        return

    def __set_quantity_levels(self) -> None:
        """Sets the quantity to buy for each safety order number."""
        prev = self.safety_order_size
        
        # first safety order
        self.quantities.append(self.safety_order_size)

        # remaining safety orders
        for _ in range(1, self.safety_orders_max):
            quantity = round(self.safety_order_volume_scale * prev, DECIMAL_MAX)
            self.quantities.append(quantity)
            prev = self.safety_order_volume_scale * prev
        return
    
    def __set_total_quantity_levels(self) -> None:
        """Sets the total quantity bought at each level."""
        prev = self.base_order_size
        
        for i in range(self.safety_orders_max):
            sum = prev + self.quantities[i]
            sum = round(sum, DECIMAL_MAX)
            self.total_quantities.append(sum)
            prev = self.total_quantities[i]
        return
    
    
    def __set_weighted_average_price_levels(self) -> None:
        """Sets the weighted average price level for each safety order number."""
        # base_order_qty = self.entry_price * self.safety_order_size
        base_order_qty = self.entry_price * self.base_order_size
        
        for i in range(self.safety_orders_max):
            numerator = 0
            for j in range(i+1):
                numerator += self.price_levels[j] * self.quantities[j]
                
            numerator += base_order_qty
            weighted_average = numerator / self.total_quantities[i]
            weighted_average = round(weighted_average, DECIMAL_MAX)
            self.average_price_levels.append(weighted_average)
        return    
    
    def __set_required_price_levels(self) -> None:
        """Sets the required price for each safety order number."""
        target_profit_decimal = (self.target_profit_percent / 100)

        # safety orders
        for i in range(self.safety_orders_max):
            required_price = self.average_price_levels[i] + (self.average_price_levels[i] * target_profit_decimal)
            required_price = round(required_price, DECIMAL_MAX)
            self.required_price_levels.append(required_price)
        return

    def __set_required_change_percentage_levels(self) -> None:
        """Sets the required change percent for each safety order number."""
        for i in range(self.safety_orders_max):
            required_change_percentage = ((self.required_price_levels[i] / self.price_levels[i]) - 1) * 100
            required_change_percentage = round(required_change_percentage, DECIMAL_MAX)
            self.required_change_percentage_levels.append(required_change_percentage)
        return
    
    def __set_profit_levels(self) -> None:
        """The more safety orders that are filled, the larger the profit will be.
        Each profit level is based on the previous profit level except for the base order."""
        
        prev = self.safety_order_size
        
        for i in range(self.safety_orders_max):
            usd_value  = self.price_levels[i] * (self.quantities[i] + prev)
            usd_profit = (self.target_profit_percent / 100) * usd_value
            usd_profit = round(usd_profit, DECIMAL_MAX)
            self.profit_levels.append(usd_profit)
            prev += self.quantities[i]
        return
    
    def __set_cost_levels(self) -> None:
        """Sets the cost (USD) spent for each safety order row."""

        for i in range(self.safety_orders_max):
            cost = self.price_levels[i] * self.quantities[i]
            cost = round(cost, DECIMAL_MAX)
            self.cost_levels.append(cost)
        return
    
    def __set_total_cost_levels(self) -> None:
        """Sets the total cost (USD) for each safety order row.
        This includes the prev order costs. """

        total_cost = self.entry_price * self.safety_order_size
        
        for i in range(self.safety_orders_max):
            total_cost += self.price_levels[i] * self.quantities[i]
            total_cost = round(total_cost, DECIMAL_MAX)
            self.total_cost_levels.append(total_cost)
        return


    def print_table(self):
        safety_order_numbers = [i for i in range(1, len(self.deviation_percentage_levels)+1)]

        self.df = pd.DataFrame(
            {
                'safety_order_number':        safety_order_numbers,
                'deviation_percentage':       self.deviation_percentage_levels,
                'quantity':                   self.quantities,
                'total_quantity':             self.total_quantities,
                'price':                      self.price_levels,
                'average_price':              self.average_price_levels,
                'required_price':             self.required_price_levels,
                'required_change_percentage': self.required_change_percentage_levels,
                'profit':                     self.profit_levels,
                'cost':                       self.cost_levels,
                'total_cost':                 self.total_cost_levels
            })
        
        self.df.set_index('safety_order_number', inplace=True)
        print(self.df)
        return
    
    def remove_top_safety_order(self) -> None:
        self.deviation_percentage_levels.pop(0)
        self.quantities.pop(0)
        self.total_quantities.pop(0)
        self.price_levels.pop(0)
        self.average_price_levels.pop(0)
        self.required_price_levels.pop(0)
        self.required_change_percentage_levels.pop(0)
        self.profit_levels.pop(0)
        self.cost_levels.pop(0)
        self.total_cost_levels.pop(0)
        return