from decimal import Decimal, InvalidOperation

from django.contrib import messages

from django.contrib.auth import (
    authenticate,
    login,
    logout,
)

from django.contrib.auth.decorators import (
    user_passes_test,
)

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.utils import timezone

from .forms import (
    CustomerOrderForm,
    CounterOrderForm,
)

from .models import (
    BraaiMaster,
    MenuItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    Shop,
    StaffProfile,
    ShopSubscriptionPayment
)
# =========================================================
# CUSTOMER ORDER PAGE
# =========================================================

def customer_order(request, shop_slug):

    shop = get_object_or_404(
        Shop,
        slug=shop_slug,
        is_active=True,
    )

    menu_items = (
        MenuItem.objects
        .filter(
            shop=shop,
            is_available=True,
        )
        .select_related(
            "category"
        )
        .order_by(
            "category__display_order",
            "category__name",
            "display_order",
            "name",
        )
    )

    # =====================================================
    # POST REQUEST
    # =====================================================

    if request.method == "POST":

        form = CustomerOrderForm(
            request.POST,
            shop=shop,
        )

        if form.is_valid():

            order = form.save(
                commit=False
            )

            order.shop = shop
            order.order_source = "online"
            order.status = "new"
            order.payment_status = "pending"
            order.estimated_total = Decimal(
                "0.00"
            )

            order.save()

            requested_total = Decimal(
                "0.00"
            )

            # =================================================
            # CREATE ORDER ITEMS
            # =================================================

            for menu_item in menu_items:

                # =============================================
                # CUSTOMER ENTERS RAND AMOUNT
                # =============================================

                if menu_item.pricing_type == "amount":

                    amount_value = request.POST.get(
                        f"amount_{menu_item.id}"
                    )

                    if not amount_value:
                        continue

                    try:

                        requested_amount = Decimal(
                            amount_value
                        )

                    except (
                        InvalidOperation,
                        TypeError,
                        ValueError,
                    ):

                        continue

                    if requested_amount <= 0:
                        continue

                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        requested_amount=requested_amount,
                        quantity=1,
                        unit_price=None,
                    )

                    requested_total += (
                        requested_amount
                    )

                # =============================================
                # FIXED PRICE ITEM
                # =============================================

                elif menu_item.pricing_type == "fixed":

                    quantity_value = request.POST.get(
                        f"quantity_{menu_item.id}",
                        "0",
                    )

                    try:

                        quantity = int(
                            quantity_value
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        quantity = 0

                    if quantity <= 0:
                        continue

                    if menu_item.price is None:
                        continue

                    line_total = (
                        menu_item.price
                        * quantity
                    )

                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        requested_amount=line_total,
                        quantity=quantity,
                        unit_price=menu_item.price,
                    )

                    requested_total += (
                        line_total
                    )

            # =================================================
            # PREVENT EMPTY ORDERS
            # =================================================

            if not order.items.exists():

                order.delete()

                form.add_error(
                    None,
                    "Please select at least one item."
                )

            # =================================================
            # SAVE VALID ORDER
            # =================================================

            else:

                order.estimated_total = (
                    requested_total
                )

                order.save(
                    update_fields=[
                        "estimated_total"
                    ]
                )

                OrderStatusHistory.objects.create(
                    order=order,
                    status="new",
                    notes="Customer placed order.",
                )

                return redirect(
                    "order_success",
                    shop_slug=shop.slug,
                    order_id=order.id,
                )

    # =====================================================
    # GET REQUEST
    # =====================================================

    else:

        form = CustomerOrderForm(
            shop=shop
        )

    # =====================================================
    # PAGE CONTEXT
    # =====================================================

    context = {
        "shop": shop,
        "form": form,
        "menu_items": menu_items,
    }

    return render(
        request,
        "orders/customer_order.html",
        context,
    )


# =========================================================
# ORDER SUCCESS PAGE
# =========================================================

def order_success(
    request,
    shop_slug,
    order_id,
):

    order = get_object_or_404(
        Order.objects
        .select_related(
            "shop",
            "braai_master",
        )
        .prefetch_related(
            "items__menu_item",
        ),
        id=order_id,
        shop__slug=shop_slug,
        shop__is_active=True,
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order
        },
    )


# =========================================================
# ACCESS CHECKS
# =========================================================

def get_staff_profile(user):

    if not user.is_authenticated:
        return None

    try:
        profile = user.staff_profile
    except StaffProfile.DoesNotExist:
        return None

    if not profile.is_active:
        return None

    if not profile.shop.is_active:
        return None

    return profile


def get_user_shop(user):

    profile = get_staff_profile(user)

    if profile is None:
        return None

    return profile.shop


def is_tenant_staff(user):

    profile = get_staff_profile(user)

    if profile is None:
        return False

    return profile.role in {
        "owner",
        "manager",
        "staff",
    }

def is_owner(user):

    return (
        user.is_authenticated
        and user.is_superuser
    )


# =========================================================
# STAFF CREATE COUNTER ORDER
# =========================================================

@user_passes_test(
    is_tenant_staff,
    login_url="/staff/login/"
)
def staff_counter_order(request):

    shop = get_user_shop(request.user)


    if not shop:
        return render(
            request,
            "orders/no_shop.html",
        )

    menu_items = (
        MenuItem.objects
        .filter(
            shop=shop,
            is_available=True,
        )
        .select_related(
            "category"
        )
        .order_by(
            "category__display_order",
            "category__name",
            "display_order",
            "name",
        )
    )

    if request.method == "POST":

        form = CounterOrderForm(
            request.POST
        )

        if form.is_valid():

            order = form.save(
                commit=False
            )

            order.shop = shop
            order.order_source = "counter"
            order.order_type = "premises"
            order.status = "new"
            order.payment_status = "pending"
            order.estimated_total = Decimal("0.00")

            order.save()

            requested_total = Decimal("0.00")

            for menu_item in menu_items:

                if menu_item.pricing_type == "amount":

                    amount_value = request.POST.get(
                        f"amount_{menu_item.id}"
                    )

                    if not amount_value:
                        continue

                    try:
                        requested_amount = Decimal(
                            amount_value
                        )
                    except (
                        InvalidOperation,
                        TypeError,
                        ValueError,
                    ):
                        continue

                    if requested_amount <= 0:
                        continue

                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        requested_amount=requested_amount,
                        quantity=1,
                        unit_price=None,
                    )

                    requested_total += requested_amount

                elif menu_item.pricing_type == "fixed":

                    quantity_value = request.POST.get(
                        f"quantity_{menu_item.id}",
                        "0",
                    )

                    try:
                        quantity = int(
                            quantity_value
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        quantity = 0

                    if quantity <= 0:
                        continue

                    if menu_item.price is None:
                        continue

                    line_total = (
                        menu_item.price
                        * quantity
                    )

                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        requested_amount=line_total,
                        quantity=quantity,
                        unit_price=menu_item.price,
                    )

                    requested_total += line_total

            if not order.items.exists():

                order.delete()

                form.add_error(
                    None,
                    "Please select at least one item."
                )

            else:

                order.estimated_total = requested_total

                order.save(
                    update_fields=[
                        "estimated_total"
                    ]
                )

                OrderStatusHistory.objects.create(
                    order=order,
                    status="new",
                    notes=(
                        "Over-the-counter order "
                        "created by staff."
                    ),
                )

                messages.success(
                    request,
                    (
                        f"Counter order #{order.id} "
                        "created successfully."
                    )
                )

                return redirect(
                    "staff_dashboard"
                )

    else:

        form = CounterOrderForm()

    context = {
        "shop": shop,
        "form": form,
        "menu_items": menu_items,
    }

    return render(
        request,
        "orders/staff_counter_order.html",
        context,
    )


# =========================================================
# STAFF LOGIN
# =========================================================

def staff_login(request):

    if request.user.is_authenticated:

        if is_tenant_staff(request.user):
            return redirect("staff_dashboard")

        logout(request)

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:

            messages.error(
                request,
                "Incorrect username or password."
            )

        elif is_tenant_staff(user):

            login(request, user)

            return redirect(
                "staff_dashboard"
            )

        else:

            messages.error(
                request,
                "This account does not have staff access."
            )

    return render(
        request,
        "orders/staff_login.html",
    )

# =========================================================
# MANAGEMENT LOGIN
# =========================================================

def owner_login(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect(
                "owner_dashboard"
            )

        logout(request)

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:

            messages.error(
                request,
                "Incorrect username or password."
            )

        elif user.is_superuser:

            login(
                request,
                user
            )

            return redirect(
                "owner_dashboard"
            )

        else:

            messages.error(
                request,
                "This account does not have management access."
            )

    return render(
        request,
        "orders/owner_login.html",
    )


# =========================================================
# STAFF DASHBOARD
# =========================================================

@user_passes_test(
    is_tenant_staff,
    login_url="/staff/login/"
)
def staff_dashboard(request):

    shop = get_user_shop(request.user)


    if not shop:
        return render(
            request,
            "orders/no_shop.html",
        )

    orders = (
        Order.objects
        .filter(
            shop=shop
        )
        .exclude(
            status__in=[
                "collected",
                "cancelled",
            ]
        )
        .select_related(
            "braai_master",
        )
        .prefetch_related(
            "items__menu_item",
        )
        .order_by(
            "-created_at"
        )
    )

    braai_masters = (
        BraaiMaster.objects
        .filter(
            shop=shop,
            is_available=True,
        )
        .order_by(
            "name"
        )
    )

    context = {
        "shop": shop,
        "orders": orders,
        "braai_masters": braai_masters,
    }

    return render(
        request,
        "orders/staff_dashboard.html",
        context,
    )


# =========================================================
# STAFF UPDATE ORDER
# =========================================================

@user_passes_test(
    is_tenant_staff,
    login_url="/staff/login/"
)
def staff_update_order(
    request,
    order_id,
):

    shop = get_user_shop(request.user)

    if not shop:
        return redirect("staff_login")

    order = get_object_or_404(
        Order,
        id=order_id,
        shop=shop,
    )

    if request.method == "POST":

        # =============================================
        # BRAAI MASTER
        # =============================================

        braai_master_id = request.POST.get(
            "braai_master"
        )

        if braai_master_id:

            order.braai_master = get_object_or_404(
                BraaiMaster,
                id=braai_master_id,
                shop=order.shop,
            )

        else:

            order.braai_master = None

        # =============================================
        # STATUS
        # =============================================

        status = request.POST.get(
            "status"
        )

        valid_statuses = dict(
            Order.STATUS_CHOICES
        )

        if status in valid_statuses:
            order.status = status

        # =============================================
        # FINAL TOTAL
        # =============================================

        final_total = request.POST.get(
            "final_total"
        )

        if final_total:

            try:

                parsed_total = Decimal(
                    final_total
                )

                if parsed_total >= 0:
                    order.final_total = parsed_total

            except (
                InvalidOperation,
                TypeError,
                ValueError,
            ):
                pass

        # =============================================
        # COUNTER ORDER PAYMENT
        # =============================================

        if order.order_source == "counter":

            payment_status = request.POST.get(
                "payment_status"
            )

            valid_payment_statuses = dict(
                Order.PAYMENT_STATUS
            )

            if payment_status in valid_payment_statuses:
                order.payment_status = payment_status

        # =============================================
        # SAVE ORDER
        # =============================================

        order.save()

        # =============================================
        # STATUS HISTORY
        # =============================================

        OrderStatusHistory.objects.create(
            order=order,
            status=order.status,
            notes="Order updated by staff.",
        )

    return redirect(
        "staff_dashboard"
    )


# =========================================================
# STAFF ORDER HISTORY
# =========================================================

@user_passes_test(
    is_tenant_staff,
    login_url="/staff/login/"
)
def staff_order_history(request):

    shop = get_user_shop(request.user)


    if not shop:
        return render(
            request,
            "orders/no_shop.html",
        )

    orders = (
        Order.objects
        .filter(
            shop=shop,
            status__in=[
                "collected",
                "cancelled",
            ]
        )
        .select_related(
            "braai_master",
        )
        .prefetch_related(
            "items__menu_item",
        )
        .order_by(
            "-updated_at"
        )
    )

    return render(
        request,
        "orders/staff_order_history.html",
        {
            "shop": shop,
            "orders": orders,
        },
    )

# =========================================================
# STAFF DAILY MANAGER REPORT
# =========================================================

@user_passes_test(
    is_tenant_staff,
    login_url="/staff/login/"
)
def staff_daily_report(request):

    shop = get_user_shop(request.user)


    if not shop:
        return render(
            request,
            "orders/no_shop.html",
        )

    # =====================================================
    # REPORT DATE
    # =====================================================

    from django.utils import timezone
    from datetime import datetime
    from django.db.models import Sum, Count, Q
    from django.db.models.functions import Coalesce

    selected_date_string = request.GET.get(
        "date"
    )

    if selected_date_string:

        try:
            selected_date = datetime.strptime(
                selected_date_string,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            selected_date = timezone.localdate()

    else:
        selected_date = timezone.localdate()

    # =====================================================
    # ORDERS FOR SELECTED DAY
    # =====================================================

    orders = (
        Order.objects
        .filter(
            shop=shop,
            created_at__date=selected_date,
        )
        .select_related(
            "braai_master",
        )
        .prefetch_related(
            "items__menu_item",
        )
        .order_by(
            "-created_at"
        )
    )

    # =====================================================
    # ORDER COUNTS
    # =====================================================

    total_orders = orders.count()

    collected_orders = orders.filter(
        status="collected"
    ).count()

    cancelled_orders = orders.filter(
        status="cancelled"
    ).count()

    new_orders = orders.filter(
        status="new"
    ).count()

    preparing_orders = orders.filter(
        status="preparing"
    ).count()

    braaiing_orders = orders.filter(
        status="braaiing"
    ).count()

    ready_orders = orders.filter(
        status="ready"
    ).count()

    in_progress_orders = orders.filter(
        status__in=[
            "new",
            "preparing",
            "braaiing",
            "ready",
        ]
    ).count()

    # =====================================================
    # ORDER SOURCES
    # =====================================================

    online_orders = orders.filter(
        order_source="online"
    ).count()

    counter_orders = orders.filter(
        order_source="counter"
    ).count()

    # =====================================================
    # ORDER TYPES
    # =====================================================

    premises_orders = orders.filter(
        order_type="premises"
    ).count()

    collection_orders = orders.filter(
        order_type="collection"
    ).count()

    # =====================================================
    # PAYMENT COUNTS
    # =====================================================

    paid_orders = orders.filter(
        payment_status="paid"
    ).count()

    pending_payment_orders = orders.filter(
        payment_status="pending"
    ).count()

    # =====================================================
    # SALES
    #
    # Cancelled orders are excluded.
    # final_total is preferred.
    # estimated_total is used when final_total is empty.
    # =====================================================

    valid_orders = orders.exclude(
        status="cancelled"
    )

    total_sales = Decimal("0.00")
    paid_sales = Decimal("0.00")
    outstanding_sales = Decimal("0.00")

    for order in valid_orders:

        amount = (
            order.final_total
            if order.final_total is not None
            else order.estimated_total
        )

        amount = amount or Decimal("0.00")

        total_sales += amount

        if order.payment_status == "paid":
            paid_sales += amount
        else:
            outstanding_sales += amount

    if valid_orders.count() > 0:

        average_order_value = (
            total_sales
            / Decimal(valid_orders.count())
        )

    else:

        average_order_value = Decimal("0.00")

    # =====================================================
    # TOP MENU ITEMS
    # =====================================================

    order_items = (
        OrderItem.objects
        .filter(
            order__shop=shop,
            order__created_at__date=selected_date,
        )
        .exclude(
            order__status="cancelled"
        )
        .select_related(
            "menu_item"
        )
    )

    item_report = {}

    for item in order_items:

        item_name = item.menu_item.name

        if item_name not in item_report:

            item_report[item_name] = {
                "name": item_name,
                "pricing_type": (
                    item.menu_item.pricing_type
                ),
                "quantity": 0,
                "order_count": 0,
                "value": Decimal("0.00"),
            }

        item_report[item_name][
            "order_count"
        ] += 1

        # Fixed-price products
        if (
            item.menu_item.pricing_type
            == "fixed"
        ):

            item_report[item_name][
                "quantity"
            ] += item.quantity

            if item.final_amount is not None:

                item_value = item.final_amount

            elif item.unit_price is not None:

                item_value = (
                    item.unit_price
                    * item.quantity
                )

            else:

                item_value = (
                    item.requested_amount
                )

        # Amount-based products such as meat
        else:

            if item.final_amount is not None:

                item_value = (
                    item.final_amount
                )

            else:

                item_value = (
                    item.requested_amount
                )

        item_report[item_name][
            "value"
        ] += (
            item_value
            or Decimal("0.00")
        )

    top_items = sorted(
        item_report.values(),
        key=lambda item: (
            item["value"],
            item["order_count"],
        ),
        reverse=True,
    )

    # =====================================================
    # BRAAI MASTER ACTIVITY
    # =====================================================

    braai_master_report = (
        orders
        .exclude(
            braai_master__isnull=True
        )
        .values(
            "braai_master__name"
        )
        .annotate(
            order_count=Count("id")
        )
        .order_by(
            "-order_count"
        )
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "shop": shop,
        "selected_date": selected_date,

        # Orders
        "orders": orders,
        "total_orders": total_orders,
        "collected_orders": collected_orders,
        "cancelled_orders": cancelled_orders,
        "in_progress_orders": in_progress_orders,

        # Individual statuses
        "new_orders": new_orders,
        "preparing_orders": preparing_orders,
        "braaiing_orders": braaiing_orders,
        "ready_orders": ready_orders,

        # Sources
        "online_orders": online_orders,
        "counter_orders": counter_orders,

        # Types
        "premises_orders": premises_orders,
        "collection_orders": collection_orders,

        # Payments
        "paid_orders": paid_orders,
        "pending_payment_orders": (
            pending_payment_orders
        ),

        # Sales
        "total_sales": total_sales,
        "paid_sales": paid_sales,
        "outstanding_sales": (
            outstanding_sales
        ),
        "average_order_value": (
            average_order_value
        ),

        # Items
        "top_items": top_items,

        # Braai masters
        "braai_master_report": (
            braai_master_report
        ),
    }

    return render(
        request,
        "orders/staff_daily_report.html",
        context,
    )


# =========================================================
# EDVANCE OWNER DASHBOARD
# =========================================================

@user_passes_test(
    is_owner,
    login_url="/owner/login/"
)
def owner_dashboard(request):

    MONTHLY_PLATFORM_FEE = Decimal("500.00")

    shops = Shop.objects.filter(
        is_active=True
    ).order_by("name")

    selected_year = request.GET.get("year")
    selected_month = request.GET.get("month")

    all_collected_orders = Order.objects.filter(
        shop__is_active=True,
        status="collected",
    )

    latest_order = (
        all_collected_orders
        .order_by("-updated_at")
        .first()
    )

    if selected_year and selected_month:
        try:
            selected_year = int(selected_year)
            selected_month = int(selected_month)

            if not 1 <= selected_month <= 12:
                raise ValueError

        except (TypeError, ValueError):
            now = timezone.now()
            selected_year = now.year
            selected_month = now.month

    elif latest_order:
        selected_year = latest_order.updated_at.year
        selected_month = latest_order.updated_at.month

    else:
        now = timezone.now()
        selected_year = now.year
        selected_month = now.month

    monthly_orders = (
        all_collected_orders
        .filter(
            updated_at__year=selected_year,
            updated_at__month=selected_month,
        )
        .select_related("shop")
        .order_by("-updated_at")
    )

    total_orders = monthly_orders.count()

    total_transaction_value = sum(
        (
            order.final_total
            if order.final_total is not None
            else order.estimated_total
            for order in monthly_orders
        ),
        Decimal("0.00")
    )

    shop_summaries = []

    total_platform_fees = Decimal("0.00")
    paid_platform_fees = Decimal("0.00")

    for shop in shops:

        shop_orders = [
            order
            for order in monthly_orders
            if order.shop_id == shop.id
        ]

        shop_transaction_value = sum(
            (
                order.final_total
                if order.final_total is not None
                else order.estimated_total
                for order in shop_orders
            ),
            Decimal("0.00")
        )

        # Fixed monthly SaaS subscription.
        subscription, created = ShopSubscriptionPayment.objects.get_or_create(
            shop=shop,
            year=selected_year,
            month=selected_month,
            defaults={
                "amount": MONTHLY_PLATFORM_FEE,
            },
        )

        shop_platform_fees = subscription.amount

        shop_paid_fees = (
            subscription.amount
            if subscription.is_paid
            else Decimal("0.00")
        )

        shop_outstanding_fees = (
            Decimal("0.00")
            if subscription.is_paid
            else subscription.amount
        )

        total_platform_fees += shop_platform_fees
        paid_platform_fees += shop_paid_fees

        shop_summaries.append({
            "shop": shop,
            "total_orders": len(shop_orders),
            "transaction_value": shop_transaction_value,
            "platform_fees": shop_platform_fees,
            "paid_fees": shop_paid_fees,
            "outstanding_fees": shop_outstanding_fees,
            "subscription": subscription,
        })

    outstanding_platform_fees = (
        total_platform_fees - paid_platform_fees
    )

    available_months = (
        all_collected_orders
        .dates("updated_at", "month", order="DESC")
    )

    context = {
        "shops": shops,
        "shop_summaries": shop_summaries,
        "orders": monthly_orders,
        "connected_shops": shops.count(),
        "total_orders": total_orders,
        "total_transaction_value": total_transaction_value,
        "total_platform_fees": total_platform_fees,
        "paid_platform_fees": paid_platform_fees,
        "outstanding_platform_fees": outstanding_platform_fees,
        "available_months": available_months,
        "selected_year": selected_year,
        "selected_month": selected_month,
        "monthly_platform_fee": MONTHLY_PLATFORM_FEE,
    }

    return render(
        request,
        "orders/owner_dashboard.html",
        context
    )


@user_passes_test(
    is_owner,
    login_url="/owner/login/"
)
def mark_platform_fees_paid(request):
    if request.method != "POST":
        return redirect("owner_dashboard")

    try:
        shop_id = int(request.POST.get("shop_id"))
        year = int(request.POST.get("year"))
        month = int(request.POST.get("month"))

        if not 1 <= month <= 12:
            raise ValueError

    except (TypeError, ValueError):
        return redirect("owner_dashboard")

    shop = get_object_or_404(
        Shop,
        id=shop_id,
        is_active=True,
    )

    subscription, created = ShopSubscriptionPayment.objects.get_or_create(
        shop=shop,
        year=year,
        month=month,
        defaults={
            "amount": Decimal("500.00"),
        },
    )

    subscription.is_paid = True
    subscription.paid_at = timezone.now()
    subscription.save(
        update_fields=[
            "is_paid",
            "paid_at",
            "updated_at",
        ]
    )

    return redirect(
        f"/owner/dashboard/?year={year}&month={month}"
    )


