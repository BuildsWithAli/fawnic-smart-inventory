from django.contrib import admin

from .models import Purchase, PurchaseItem, Sale, SaleItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    inlines = [PurchaseItemInline]
    list_display = ["id", "supplier", "date", "created_at"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]
    list_display = ["id", "customer", "date", "status", "created_at"]
