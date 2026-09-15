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
)
# =========================================================
# CUSTOMER ORDER PAGE
# =========================================================

def customer_order(request):

    shop = Shop.objects.filter(
        is_active=True
    ).first()

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

def is_hlophe_staff(user):

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.groups.filter(
        name="Hlophe Staff"
    ).exists()


def is_owner(user):

    return (
        user.is_authenticated
        and user.is_superuser
    )


# =========================================================
# STAFF CREATE COUNTER ORDER
# =========================================================

@user_passes_test(
    is_hlophe_staff,
    login_url="/staff/login/"
)
def staff_counter_order(request):

    shop = Shop.objects.filter(
        is_active=True
    ).first()

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
                        "created by Hlophe staff."
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

        if request.user.is_superuser:
            return redirect("staff_dashboard")

        if request.user.groups.filter(
            name="Hlophe Staff"
        ).exists():
            return redirect("staff_dashboard")

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

        elif (
            user.is_superuser
            or user.groups.filter(
                name="Hlophe Staff"
            ).exists()
        ):

            login(
                request,
                user
            )

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
    is_hlophe_staff,
    login_url="/staff/login/"
)
def staff_dashboard(request):

    shop = Shop.objects.filter(
        is_active=True
    ).first()

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
    is_hlophe_staff,
    login_url="/staff/login/"
)
def staff_update_order(
    request,
    order_id,
):

    order = get_object_or_404(
        Order,
        id=order_id,
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
            notes="Order updated by Hlophe staff.",
        )

    return redirect(
        "staff_dashboard"
    )


# =========================================================
# STAFF ORDER HISTORY
# =========================================================

@user_passes_test(
    is_hlophe_staff,
    login_url="/staff/login/"
)
def staff_order_history(request):

    shop = Shop.objects.filter(
        is_active=True
    ).first()

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
# EDVANCE OWNER DASHBOARD
# =========================================================

@user_passes_test(
    is_owner,
    login_url="/owner/login/"
)
def owner_dashboard(request):

    shop = Shop.objects.filter(
        is_active=True
    ).first()

    if not shop:
        return render(
            request,
            "orders/no_shop.html",
        )

    # =============================================
    # SELECTED MONTH
    # =============================================

    selected_year = request.GET.get(
        "year"
    )

    selected_month = request.GET.get(
        "month"
    )

    # =============================================
    # ALL COLLECTED ORDERS
    # =============================================

    collected_orders = (
        Order.objects
        .filter(
            shop=shop,
            status="collected",
        )
    )

    # =============================================
    # DEFAULT MONTH
    # =============================================

    latest_order = (
        collected_orders
        .order_by(
            "-updated_at"
        )
        .first()
    )

    if selected_year and selected_month:

        try:

            selected_year = int(
                selected_year
            )

            selected_month = int(
                selected_month
            )

            if not 1 <= selected_month <= 12:

                raise ValueError

        except (
            TypeError,
            ValueError,
        ):

            now = timezone.now()

            selected_year = (
                now.year
            )

            selected_month = (
                now.month
            )

    elif latest_order:

        selected_year = (
            latest_order.updated_at.year
        )

        selected_month = (
            latest_order.updated_at.month
        )

    else:

        now = timezone.now()

        selected_year = (
            now.year
        )

        selected_month = (
            now.month
        )

    # =============================================
    # MONTHLY ORDERS
    # =============================================

    monthly_orders = (
        collected_orders
        .filter(
            updated_at__year=selected_year,
            updated_at__month=selected_month,
        )
        .order_by(
            "-updated_at"
        )
    )

    # =============================================
    # COMPLETED ORDERS
    # =============================================

    total_orders = (
        monthly_orders.count()
    )

    # =============================================
    # TOTAL PLATFORM FEES
    # =============================================

    total_platform_fees = sum(
        (
            order.platform_fee
            for order
            in monthly_orders
        ),
        Decimal("0.00")
    )

    # =============================================
    # PAID PLATFORM FEES
    # =============================================

    paid_platform_fees = sum(
        (
            order.platform_fee
            for order
            in monthly_orders
            if order.platform_fee_paid
        ),
        Decimal("0.00")
    )

    # =============================================
    # OUTSTANDING PLATFORM FEES
    # =============================================

    outstanding_platform_fees = (
        total_platform_fees
        - paid_platform_fees
    )

    # =============================================
    # AVAILABLE MONTHS
    # =============================================

    available_months = (
        collected_orders
        .dates(
            "updated_at",
            "month",
            order="DESC",
        )
    )

    # =============================================
    # PAGE CONTEXT
    # =============================================

    context = {
        "shop": shop,
        "orders": monthly_orders,
        "total_orders": total_orders,
        "total_platform_fees": (
            total_platform_fees
        ),
        "paid_platform_fees": (
            paid_platform_fees
        ),
        "outstanding_platform_fees": (
            outstanding_platform_fees
        ),
        "available_months": (
            available_months
        ),
        "selected_year": (
            selected_year
        ),
        "selected_month": (
            selected_month
        ),
    }

    return render(
        request,
        "orders/owner_dashboard.html",
        context,
    )


# =========================================================
# MARK SELECTED MONTH PLATFORM FEES AS PAID
# =========================================================

@user_passes_test(
    is_owner,
    login_url="/owner/login/"
)
def mark_platform_fees_paid(request):

    if request.method != "POST":

        return redirect(
            "owner_dashboard"
        )

    shop = Shop.objects.filter(
        is_active=True
    ).first()

    if not shop:

        return redirect(
            "owner_dashboard"
        )

    try:

        year = int(
            request.POST.get(
                "year"
            )
        )

        month = int(
            request.POST.get(
                "month"
            )
        )

        if not 1 <= month <= 12:

            raise ValueError

    except (
        TypeError,
        ValueError,
    ):

        return redirect(
            "owner_dashboard"
        )

    Order.objects.filter(
        shop=shop,
        status="collected",
        platform_fee_paid=False,
        updated_at__year=year,
        updated_at__month=month,
    ).update(
        platform_fee_paid=True
    )

    return redirect(
        f"/owner/dashboard/"
        f"?year={year}&month={month}"
    )
