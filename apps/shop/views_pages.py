"""Store UI pages: cart, checkout, order confirmation, admin financial report."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Order, Payment, Product
from .store import add_to_cart, checkout, financial_report, remove_from_cart, set_quantity


@login_required
def cart_view(request):
    from .store import get_cart
    cart = get_cart(request.user)
    context = {'segment': 'cart', 'cart': cart}
    return render(request, 'shop/cart.html', context)


@login_required
def cart_add(request):
    if request.method == 'POST':
        try:
            add_to_cart(request.user, request.POST.get('product_id'), request.POST.get('quantity', 1))
        except ValueError:
            pass
    return redirect('/cart')


@login_required
def cart_remove(request, item_id):
    if request.method == 'POST':
        remove_from_cart(request.user, item_id)
    return redirect('/cart')


@login_required
def cart_set_qty(request, item_id):
    if request.method == 'POST':
        try:
            set_quantity(request.user, item_id, int(request.POST.get('quantity', 0)))
        except ValueError:
            pass
    return redirect('/cart')


@login_required
def checkout_view(request):
    from .store import get_cart
    cart = get_cart(request.user)
    placed = None
    if request.method == 'POST':
        try:
            order, payment = checkout(
                request.user,
                card_token=request.POST.get('card_token') or None,
                hub_ref=request.POST.get('hub_ref') or None,
                payment_method=request.POST.get('payment_method', 'card'),
            )
            placed = {'order': order, 'payment': payment}
        except ValueError as e:
            error = str(e)
            placed = {'error': error}
    context = {
        'segment': 'cart',
        'cart': cart,
        'placed': placed,
        'products': Product.objects.filter(active=True),
    }
    return render(request, 'shop/checkout.html', context)


@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'payments')
    return render(request, 'shop/orders.html', {'segment': 'orders', 'orders': orders, 'Order': Order})


@login_required
def financial_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('/dashboard')
    report = financial_report()
    return render(request, 'shop/financial.html', {'segment': 'financial', 'report': report, 'Order': Order})


@login_required
def health_view(request):
    """Sysop / business-manager status page — reads the same payload as
    /api/v1/health and /mcp/health_check (hub polls any of the three)."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('/dashboard')
    from .services import service_health
    return render(request, 'shop/health.html', {'segment': 'health', 'health': service_health()})