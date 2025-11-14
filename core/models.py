from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100, blank=True)  # optional internal code / SKU

    # Warehouse picking order: 1, 2, 3, ... (used to sort for the warehouse route)
    pick_order = models.PositiveIntegerField()

    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit = models.CharField(max_length=50, blank=True)  # e.g. "piece", "box", "kg"

    # Whether the product should appear in the order form
    is_active = models.BooleanField(default=True)

    # Image for the product (optional)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        # How the product will be shown in admin / logs
        return f"{self.name} ({self.code})" if self.code else self.name