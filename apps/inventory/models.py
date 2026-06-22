# apps/inventory/models.py
from django.db import models

class Inventory(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    product = models.OneToOneField('products.Product', on_delete=models.CASCADE)
    
    # Stock
    stock_quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)
    available_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    
    # Warehouse
    warehouse_location = models.CharField(max_length=100, blank=True)
    shelf_location = models.CharField(max_length=50, blank=True)
    bin_number = models.CharField(max_length=50, blank=True)
    
    # Reorder
    reorder_point = models.IntegerField(default=10)
    reorder_quantity = models.IntegerField(default=50)
    last_restock_date = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    in_transit_quantity = models.IntegerField(default=0)
    damaged_quantity = models.IntegerField(default=0)
    
    # AI Data
    forecast_demand = models.JSONField(null=True, blank=True)  # Daily forecast
    optimal_stock = models.IntegerField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_inventory'
    
    def __str__(self):
        return f"{self.product.name} - {self.stock_quantity}"