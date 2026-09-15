from django.contrib import admin

from .models import (
    Shop,
    BraaiMaster,
    Category,
    MenuItem,
    Order,
    OrderItem,
    OrderStatusHistory,
)


# =========================================================
# SHOP ADMIN
# =========================================================

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "phone_number",
        "whatsapp_number",
        "location",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "phone_number",
        "whatsapp_number",
        "location",
    )


# =========================================================
# BRAAI MASTER ADMIN
# =========================================================

@admin.register(BraaiMaster)
class BraaiMasterAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "shop",
        "is_available",
    )

    list_filter = (
        "shop",
        "is_available",
    )

    search_fields = (
        "name",
    )


# =========================================================
# CATEGORY ADMIN
# =========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "shop",
        "display_order",
        "is_active",
    )

    list_filter = (
        "shop",
        "is_active",
    )

    ordering = (
        "shop",
        "display_order",
        "name",
    )


# =========================================================
# MENU ITEM ADMIN
# =========================================================

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "shop",
        "category",
        "pricing_type",
        "price",
        "display_order",
        "is_available",
    )

    list_filter = (
        "shop",
        "category",
        "pricing_type",
        "is_available",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "category",
        "display_order",
        "name",
    )


# =========================================================
# ORDER ITEM INLINE
# =========================================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem
    extra = 0

    fields = (
        "menu_item",
        "requested_amount",
        "quantity",
        "unit_price",
        "final_amount",
    )


# =========================================================
# ORDER STATUS HISTORY INLINE
# =========================================================

class OrderStatusHistoryInline(admin.TabularInline):

    model = OrderStatusHistory
    extra = 0

    readonly_fields = (
        "created_at",
    )


# =========================================================
# ORDER ADMIN
# =========================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer_name",
        "shop",
        "braai_master",
        "order_type",
        "status",
        "estimated_total",
        "final_total",
        "payment_status",
        "created_at",
    )

    list_filter = (
        "shop",
        "order_type",
        "status",
        "payment_status",
    )

    search_fields = (
        "customer_name",
        "whatsapp_number",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        OrderItemInline,
        OrderStatusHistoryInline,
    )


# =========================================================
# ORDER ITEM ADMIN
# =========================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "menu_item",
        "requested_amount",
        "quantity",
        "unit_price",
        "final_amount",
    )

    list_filter = (
        "menu_item",
    )

    search_fields = (
        "order__customer_name",
        "menu_item__name",
    )


# =========================================================
# ORDER STATUS HISTORY ADMIN
# =========================================================

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
    )

    ordering = (
        "-created_at",
    )