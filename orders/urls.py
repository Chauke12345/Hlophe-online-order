from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

    # =========================================================
    # PUBLIC PLATFORM HOMEPAGE
    # =========================================================

    path(
        "",
        views.home,
        name="home",
    ),

    # =========================================================
    # CUSTOMER
    # =========================================================

    path(
        "shop/<slug:shop_slug>/",
        views.customer_order,
        name="customer_order",
    ),

    path(
        "shop/<slug:shop_slug>/order/<int:order_id>/success/",
        views.order_success,
        name="order_success",
    ),


    # =========================================================
    # STAFF LOGIN / LOGOUT
    # =========================================================

    path(
        "staff/login/",
        views.staff_login,
        name="staff_login",
    ),

    path(
        "staff/logout/",
        auth_views.LogoutView.as_view(
            next_page="staff_login"
        ),
        name="staff_logout",
    ),

# =========================================================
# STAFF
# =========================================================

path(
    "staff/counter-order/",
    views.staff_counter_order,
    name="staff_counter_order",
),

path(
    "staff/dashboard/",
    views.staff_dashboard,
    name="staff_dashboard",
),

path(
    "staff/order/<int:order_id>/update/",
    views.staff_update_order,
    name="staff_update_order",
),

path(
    "staff/history/",
    views.staff_order_history,
    name="staff_order_history",
),

path(
    "staff/reports/daily/",
    views.staff_daily_report,
    name="staff_daily_report",
),

    # =========================================================
    # MANAGEMENT LOGIN / LOGOUT
    # =========================================================

    path(
        "owner/login/",
        views.owner_login,
        name="owner_login",
    ),

    path(
        "owner/logout/",
        auth_views.LogoutView.as_view(
            next_page="owner_login"
        ),
        name="owner_logout",
    ),


    # =========================================================
    # MANAGEMENT / OWNER
    # =========================================================

    path(
        "owner/dashboard/",
        views.owner_dashboard,
        name="owner_dashboard",
    ),

    path(
        "owner/mark-fees-paid/",
        views.mark_platform_fees_paid,
        name="mark_platform_fees_paid",
    ),

]
