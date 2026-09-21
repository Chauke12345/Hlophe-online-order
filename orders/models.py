from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models


# =========================================================
# SHOP / TENANT
# =========================================================

class Shop(models.Model):

    name = models.CharField(
        max_length=150
    )

    # Unique tenant identifier used in URLs.
    # Example:
    # /shop/example-shisanyama/
    slug = models.SlugField(
        max_length=160,
        unique=True,
        null=True,
        blank=True,
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
# STAFF PROFILE
# =========================================================

class StaffProfile(models.Model):

    ROLE_CHOICES = [
        (
            "owner",
            "Owner",
        ),
        (
            "manager",
            "Manager",
        ),
        (
            "staff",
            "Staff",
        ),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="staff_profiles",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="staff",
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.shop.name} - "
            f"{self.get_role_display()}"
        )


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
        (
            "amount",
            "Customer Enters Amount",
        ),
        (
            "fixed",
            "Fixed Price",
        ),
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
        return f"{self.name} - {self.shop.name}"

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
            "Ordering at Premises",
        ),
        (
            "collection",
            "Order for Collection",
        ),
    ]

    # How the order entered the system.
    ORDER_SOURCE_CHOICES = [
        (
            "online",
            "Online",
        ),
        (
            "counter",
            "Over the Counter",
        ),
    ]

    STATUS_CHOICES = [
        (
            "new",
            "Order Received",
        ),
        (
            "preparing",
            "Preparing Order",
        ),
        (
            "braaiing",
            "Braaiing",
        ),
        (
            "ready",
            "Ready for Collection",
        ),
        (
            "collected",
            "Collected",
        ),
        (
            "cancelled",
            "Cancelled",
        ),
    ]

    PAYMENT_STATUS = [
        (
            "pending",
            "Payment Pending",
        ),
        (
            "paid",
            "Paid",
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

    # Customer information.
    customer_name = models.CharField(
        max_length=150
    )

    whatsapp_number = models.CharField(
        max_length=20,
        blank=True
    )

    # Where the customer is ordering from.
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPES
    )

    # How the order entered the system.
    order_source = models.CharField(
        max_length=20,
        choices=ORDER_SOURCE_CHOICES,
        default="online"
    )

    # Current progress of the order.
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

    # Final amount confirmed by the tenant/shop.
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

    # Whether the tenant has settled this
    # platform fee with EdVance Tech.
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
            f"{self.customer_name} - "
            f"{self.shop.name}"
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
    # on this specific product.
    requested_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Amount confirmed by the tenant/shop
    # after the product has been prepared/weighed.
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Used for fixed-price items.
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

class ShopSubscriptionPayment(models.Model):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
    )

    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("500.00"),
    )

    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "year", "month"],
                name="unique_shop_monthly_subscription",
            )
        ]
        ordering = ["-year", "-month", "shop__name"]

    def __str__(self):
        return (
            f"{self.shop.name} - "
            f"{self.year}-{self.month:02d} - "
            f"R{self.amount}"
        )

