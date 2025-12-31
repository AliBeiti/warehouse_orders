from django.db import models
from decimal import Decimal
from django.utils import timezone

class Category(models.Model):
    """
    Category is now hierarchical:
    - parent = None  -> main category (for your 5–7 main pages)
    - parent != None -> sub category (for collapsible sections inside a main page)
    """
    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveIntegerField(default=0)

    # NEW: parent category for subcategories
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subcategories',
        null=True,
        blank=True,
        help_text="Leave empty for MAIN categories. Set a parent to make this a SUB category."
    )

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def is_main(self):
        """True if this is a main category (no parent)."""
        return self.parent is None

    @property
    def is_sub(self):
        return self.parent is not None


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

    # Base price (what you had already). We’ll treat this as the price BEFORE discount.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )

    # NEW: percentage discount (offers like -20%, -30%, etc.)
    discount_percent = models.PositiveIntegerField(
        default=0,
        help_text="Percentage discount (0–100). 0 means no discount."
    )

    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="If set, this final price overrides the percentage discount."
    )
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

    @property
    def final_price(self):
        """
        Final selling price logic:
        1. If discount_price is set -> use that.
        2. Else if discount_percent > 0 -> price * (100 - discount_percent) / 100.
        3. Else -> price.
        """
        from decimal import Decimal

        if self.price is None:
            return None

        # 1) Manual override
        if self.discount_price is not None:
            return self.discount_price

        # 2) Percentage discount
        if self.discount_percent:
            factor = Decimal(100 - self.discount_percent) / Decimal(100)
            return (self.price * factor).quantize(Decimal("0.01"))

        # 3) No discount
        return self.price


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=50, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_note = models.TextField(blank=True)
    
    customer_type = models.CharField(
        max_length=20,
        choices=[('retail', 'Perakende'), ('wholesale', 'Toptan')],
        default='retail'
    )
    
    is_confirmed = models.BooleanField(default=False)
    printed = models.BooleanField(default=False)
    printed_at = models.DateTimeField(null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

class DiscountTier(models.Model):
    threshold = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum order amount in TL")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Discount percentage")
    customer_type = models.CharField(
        max_length=20,
        choices=[('retail', 'Perakende'), ('wholesale', 'Toptan')],
        default='retail',
        help_text="Customer type this discount applies to"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['customer_type', 'threshold']
        verbose_name = 'Discount Tier'
        verbose_name_plural = 'Discount Tiers'
    
    def __str__(self):
        return f"{self.get_customer_type_display()} - {self.threshold} TL → {self.discount_percentage}%"