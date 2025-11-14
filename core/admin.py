from django.contrib import admin
from .models import Product
# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'pick_order', 'price', 'unit', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('pick_order', 'name')
    list_editable = ('pick_order', 'price', 'unit', 'is_active')  # quick edits from list
