from django.contrib import admin
from .models import Category,Product, Order,OrderItem
from django.utils.html import format_html
from django.urls import reverse
# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order")
    ordering = ("display_order", "name")
    list_editable = ("display_order",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "display_order", "pick_order", "price", "unit", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name", "code")
    ordering = ("category", "display_order", "name")
    list_editable = ("category", "display_order", "pick_order", "price", "unit", "is_active")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "created_at", "csv_download_link")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    def csv_download_link(self, obj):
        url = reverse("order_csv_admin", args=[obj.id])
        return format_html('<a href="{}">Download CSV</a>', url)

    csv_download_link.short_description = "CSV"