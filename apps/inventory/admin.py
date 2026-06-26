from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    # লিস্ট ভিউতে স্টক কন্ডিশন দ্রুত বোঝার জন্য গুরুত্বপূর্ণ কলাম
    list_display = (
        'product', 
        'tenant', 
        'stock_quantity', 
        'reserved_quantity', 
        'available_quantity', 
        'low_stock_status'
    )
    
    # ফিল্টার অপশন
    list_filter = ('tenant', 'warehouse_location')
    
    # সার্চ অপশন
    search_fields = ('product__name', 'warehouse_location', 'bin_number')
    
    # ফিল্ডসেট ডিজাইন
    fieldsets = (
        ('Product & Warehouse', {
            'fields': ('tenant', 'product', 'warehouse_location', 'shelf_location', 'bin_number')
        }),
        ('Stock Levels', {
            'fields': ('stock_quantity', 'reserved_quantity', 'available_quantity', 'in_transit_quantity', 'damaged_quantity')
        }),
        ('Reorder Settings', {
            'fields': ('low_stock_threshold', 'reorder_point', 'reorder_quantity', 'last_restock_date')
        }),
        ('AI Intelligence', {
            'fields': ('forecast_demand', 'optimal_stock'),
            'classes': ('collapse',) # ডেটা অনেক বড় হলে কলাপস থাকবে
        }),
    )
    
    readonly_fields = ('updated_at',)
    
    # লো-স্টক চেক করার জন্য একটি মেথড (কালার কোডিং সুবিধা দিতে পারে)
    @admin.display(description="Stock Status")
    def low_stock_status(self, obj):
        if obj.stock_quantity <= obj.low_stock_threshold:
            return "⚠️ Low Stock"
        return "✅ Healthy"

    ordering = ('-stock_quantity',)