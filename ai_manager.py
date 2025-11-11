import random

class AIManager:
    def dynamic_pricing(self, products):
        for product in products:
            demand_factor = random.uniform(0.9, 1.2)
            stock_factor = 1.05 if product['stock'] < 5 else 1.0
            new_price = round(product['price'] * demand_factor * stock_factor, 2)
            product['price'] = new_price
        print("AI Manager updated prices dynamically.")
        return products
