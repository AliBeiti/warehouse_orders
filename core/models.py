from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100, blank=True)  # optional internal code / SKU

    # Warehouse picking order: 1, 2, 3, ... (used to sort for the warehouse route)
    pick_order = models.PositiveIntegerField()
    display_order = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit = models.CharField(max_length=50, blank=True)  # e.g. "piece", "box", "kg"

    # Whether the product should appear in the order form
    is_active = models.BooleanField(default=True)

    # Image for the product (optional)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        # How the product will be shown in admin / logs
        return f"{self.name} ({self.code})" if self.code else self.name

    
class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=50, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_note = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} ({self.created_at:%Y-%m-%d})"
    

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

