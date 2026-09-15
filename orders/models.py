from django.db import models
from decimal import Decimal


# =========================================================
# SHOP
# =========================================================

class Shop(models.Model):

    name = models.CharField(
        max_length=150
    )

    phone_number = models.CharField(
        max_length=20
    )

    whatsapp_number = models.CharField(
        max_length=20
    )

    address = models.TextField(
        blank=True
    )

    location = models.CharField(
        max_length=150,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# =========================================================
# BRAAI MASTER
# =========================================================

class BraaiMaster(models.Model):

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="braai_masters"
    )

    name = models.CharField(
        max_length=100
    )

    is_available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} - {self.shop.name}"


# =========================================================
# MENU CATEGORY
# =========================================================

class Category(models.Model):

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="categories"
    )

    name = models.CharField(
        max_length=100
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.name} - {self.shop.name}"

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]

        verbose_name_plural = "Categories"


# =========================================================
# MENU ITEM
# =========================================================
class MenuItem(models.Model):

    PRICING_TYPES = [
        ("amount", "Customer Enters Amount"),
        ("fixed", "Fixed Price"),
    ]

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="menu_items"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_items"
    )

    name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    pricing_type = models.CharField(
        max_length=20,
        choices=PRICING_TYPES,
        default="amount"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to="menu_items/",
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    is_available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]

# =========================================================
# CUSTOMER ORDER
# =========================================================
class Order(models.Model):

    ORDER_TYPES = [
        (
            "premises",
            "Ordering at Hlophe"
        ),
        (
            "collection",
            "Order for Collection"
        ),
    ]

    # How the order entered the system
    ORDER_SOURCE_CHOICES = [
        (
            "online",
            "Online"
        ),
        (
            "counter",
            "Over the Counter"
        ),
    ]

    STATUS_CHOICES = [
        (
            "new",
            "Order Received"
        ),
        (
            "preparing",
            "Preparing Order"
        ),
        (
            "braaiing",
            "Braaiing"
        ),
        (
            "ready",
            "Ready for Collection"
        ),
        (
            "collected",
            "Collected"
        ),
        (
            "cancelled",
            "Cancelled"
        ),
    ]

    PAYMENT_STATUS = [
        (
            "pending",
            "Payment Pending"
        ),
        (
            "paid",
            "Paid"
        ),
    ]

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    braai_master = models.ForeignKey(
        BraaiMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    # Customer information
    customer_name = models.CharField(
        max_length=150
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True
    )

    # Where the customer is ordering from
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPES
    )

    # How the order entered the system
    order_source = models.CharField(
        max_length=20,
        choices=ORDER_SOURCE_CHOICES,
        default="online"
    )

    # Current progress of the order
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new"
    )

    # Total amount requested by the customer.
    estimated_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # Final amount confirmed by Hlophe.
    final_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Internal EdVance platform fee.
    # Not displayed to the customer.
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("15.00")
    )

    # Whether Hlophe has settled this
    # platform fee with EdVance.
    platform_fee_paid = models.BooleanField(
        default=False
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending"
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"Order #{self.id} - "
            f"{self.customer_name}"
        )
# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT
    )

    # Amount the customer wants to spend
    # on this specific meat/product.
    #
    # Example:
    # Beef = R150
    # Wors = R100
    requested_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Amount confirmed by Hlophe after
    # the meat has been prepared/weighed.
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Used for fixed-price items such as
    # Pap, Chakalaka, Coleslaw and drinks.
    quantity = models.PositiveIntegerField(
        default=1
    )

    # Price per fixed-price item at the time
    # the customer placed the order.
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):

        return (
            f"{self.menu_item.name} - "
            f"R{self.requested_amount} - "
            f"Order #{self.order.id}"
        )
# =========================================================
# ORDER STATUS HISTORY
# =========================================================

class OrderStatusHistory(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history"
    )

    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "created_at",
        ]

        verbose_name_plural = (
            "Order status histories"
        )

    def __str__(self):

        return (
            f"Order #{self.order.id} - "
            f"{self.get_status_display()}"
        )

