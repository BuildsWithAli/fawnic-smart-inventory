from django.contrib import admin

from .models import Brand, Category, Product, StockAdjustment, Warehouse

admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(Warehouse)
admin.site.register(Product)
admin.site.register(StockAdjustment)
