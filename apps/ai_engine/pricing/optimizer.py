# apps/ai_engine/pricing/optimizer.py
import numpy as np
from scipy.optimize import minimize

class DynamicPricingEngine:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
    
    def optimize_price(self, product_data):
        """Optimize price based on demand, competition, and inventory"""
        
        # Extract data
        current_price = product_data['price']
        demand_elasticity = product_data.get('elasticity', 1.5)
        inventory_level = product_data['inventory']
        competitor_price = product_data.get('competitor_price', None)
        seasonality_factor = product_data.get('seasonality', 1.0)
        
        # Define price bounds
        min_price = current_price * 0.7
        max_price = current_price * 1.3
        
        # Demand function
        def demand(price, base_demand=1000):
            return base_demand * (price ** -demand_elasticity) * seasonality_factor
        
        # Revenue function to maximize
        def revenue(price):
            units_sold = demand(price)
            return -price * units_sold  # Negative for minimization
        
        # Constraints
        constraints = [
            {'type': 'ineq', 'fun': lambda x: x - min_price},  # x >= min_price
            {'type': 'ineq', 'fun': lambda x: max_price - x},  # x <= max_price
        ]
        
        # Inventory constraint (can't sell more than available)
        if inventory_level < 100:
            def inventory_constraint(price):
                return inventory_level - demand(price)
            constraints.append({'type': 'ineq', 'fun': inventory_constraint})
        
        # Competitor price constraint
        if competitor_price:
            def competitor_constraint(price):
                return (price - competitor_price) / competitor_price * 100
            constraints.append({'type': 'ineq', 'fun': competitor_constraint})
        
        # Optimize
        result = minimize(
            revenue, 
            x0=[current_price], 
            method='SLSQP',
            constraints=constraints
        )
        
        optimal_price = result.x[0]
        
        return {
            'optimal_price': optimal_price,
            'current_price': current_price,
            'percent_change': ((optimal_price - current_price) / current_price) * 100,
            'strategy': self._determine_strategy(optimal_price, current_price)
        }
    
    def _determine_strategy(self, optimal, current):
        """Determine pricing strategy used"""
        if optimal > current:
            return "increase_price"
        elif optimal < current:
            return "decrease_price"
        else:
            return "maintain_price"