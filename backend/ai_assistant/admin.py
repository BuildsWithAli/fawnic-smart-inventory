from django.contrib import admin

from .models import StockAlert


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "order", "severity", "resolved", "created_at"]
    list_filter = ["severity", "resolved"]
