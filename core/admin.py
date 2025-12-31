from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Category, Product, Order, OrderItem, DiscountTier


# ==============================
# CATEGORY ADMIN (main + sub)
# ==============================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # 🔹 We keep what you had and add parent + is_main_display for clarity
    list_display = ("name", "parent","color_code", "display_order", "is_main_display")
    ordering = ("display_order", "name")
    list_editable = ("display_order","color_code")
    list_filter = ("parent",)
    search_fields = ("name",)

    def is_main_display(self, obj):
        """
        Shows True if this is a main category (no parent).
        """
        return obj.parent is None

    is_main_display.boolean = True
    is_main_display.short_description = "Main category"


# ==============================
# PRODUCT ADMIN
# ==============================


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "category",
        "display_order",
        "pick_order",
        "price",
        "discount_percent",
        "discount_price",       # NEW
        "final_price_display",
        "unit",
        "is_active",
    )
    list_filter = ("is_active", "category")
    search_fields = ("name", "code")
    ordering = ("category", "display_order", "name")

    list_editable = (
        "category",
        "display_order",
        "pick_order",
        "price",
        "discount_percent",
        "discount_price",       # NEW
        "unit",
        "is_active",
    )

    def final_price_display(self, obj):
        return obj.final_price
    final_price_display.short_description = "Final price"


# ==============================
# ORDER & ORDER ITEMS ADMIN
# ==============================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "customer_name", 
        "customer_type",           # ADD THIS
        "created_at", 
        "is_confirmed",            # ADD THIS
        "subtotal",                # ADD THIS
        "discount_percentage",     # ADD THIS
        "final_total",             # ADD THIS
        "printed",                 # ADD THIS
        "csv_download_link"
    )
    list_filter = ("customer_type", "is_confirmed", "printed")  # ADD THIS
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    def csv_download_link(self, obj):
        url = reverse("order_csv_admin", args=[obj.id])
        return format_html('<a href="{}">Download CSV</a>', url)

    csv_download_link.short_description = "CSV"


# Optional: you can register OrderItem if you want a separate admin view,
# but it's not required because you already manage it via the inline.
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity")
    list_filter = ("order__created_at", "product__category")
    search_fields = ("order__id", "product__name")


@admin.register(DiscountTier)
class DiscountTierAdmin(admin.ModelAdmin):
    list_display = ['customer_type', 'threshold', 'discount_percentage', 'is_active', 'created_at']
    list_filter = ['customer_type', 'is_active']
    list_editable = ['is_active']
    ordering = ['customer_type', 'threshold']