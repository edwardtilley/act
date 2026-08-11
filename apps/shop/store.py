"""Store service layer: cart + checkout + reporting — shared by UI, API and MCP.

This is the single source of truth for store operations so every surface
(HTML pages, /api/v1 REST, /mcp JSON-RPC-style endpoints) behaves identically.
"""

from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem, Payment, Product
from .services import charge_via_hub


def get_cart(user):
    """Get (or lazily create) the user's shopping cart."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def add_to_cart(user, product_id, quantity=1):
    """Add a product to the user's cart. Creates the cart if missing."""
    product = Product.objects.filter(pk=product_id, active=True).first()
    if not product:
        raise ValueError('Unknown or inactive product_id=%s' % product_id)
    qty = max(1, int(quantity or 1))
    cart = get_cart(user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += qty
    else:
        item.quantity = qty
    item.save()
    return cart


def remove_from_cart(user, item_id):
    cart = get_cart(user)
    CartItem.objects.filter(pk=item_id, cart=cart).delete()
    return cart


def clear_cart(cart):
    cart.items.all().delete()


def set_quantity(user, item_id, quantity):
    cart = get_cart(user)
    item = CartItem.objects.filter(pk=item_id, cart=cart).first()
    if not item:
        raise ValueError('Cart item not found')
    if quantity and quantity > 0:
        item.quantity = quantity
        item.save()
    else:
        item.delete()
    return cart


def checkout(user, card_token=None, hub_ref=None, payment_method='card'):
    """Turn the user's cart into an Order and charge it via the hub gateway.

    Returns (order, payment). Raises ValueError on empty cart.
    The hub gateway charge happens synchronously; orders are marked paid
    only on gateway success.
    """
    cart = get_cart(user)
    items = list(cart.items.select_related('product').all())
    if not items:
        raise ValueError('Cart is empty — nothing to check out.')

    total_cents = cart.total_cents
    order = Order.objects.create(
        user=user,
        status=Order.STATUS_PENDING,
        total_cents=total_cents,
        payment_method=payment_method,
    )
    for item in items:
        order.items.create(
            product=item.product,
            name=item.product.name,
            price_cents=item.product.price_cents,
            quantity=item.quantity,
        )

    result = charge_via_hub(order, total_cents, card_token=card_token, hub_ref=hub_ref)
    payment = Payment.objects.create(
        order=order,
        gateway=result['gateway'],
        gateway_transaction_id=result['transaction_id'],
        amount_cents=total_cents,
        status=Payment.STATUS_SUCCEEDED if result['status'] == 'succeeded' else Payment.STATUS_FAILED,
        raw_response=result['raw'],
    )
    if payment.status == Payment.STATUS_SUCCEEDED:
        order.status = Order.STATUS_PAID
        order.paid_at = timezone.now()
        order.save()
        cart.items.all().delete()
    else:
        order.status = Order.STATUS_FAILED
        order.save()
    return order, payment


class StoreError(Exception):
    pass


# ── Financial reporting (shared by UI and admin) ──────────────────────────────


def financial_report():
    """Revenue overview shared by the /admin/financial page, /api/v1/reports
    and /mcp/financial_check."""
    from .services import money_display

    paid = Order.objects.filter(status=Order.STATUS_PAID)
    total_revenue = sum(o.total_cents for o in paid)
    paid_count = paid.count()

    by_product = {}
    for oi in OrderItem.objects.filter(order__status=Order.STATUS_PAID).select_related('product'):
        key = oi.product.name if oi.product else oi.name
        by_product[key] = by_product.get(key, 0) + oi.subtotal_cents

    by_month = {}
    for o in paid.filter(paid_at__isnull=False):
        key = o.paid_at.strftime('%Y-%m')
        by_month[key] = by_month.get(key, 0) + o.total_cents

    by_status = {}
    for status, label in Order.STATUSES:
        by_status[status] = Order.objects.filter(status=status).count()

    payments = Payment.objects.order_by('-created_at')[:100]
    return {
        'generated_at': timezone.now().isoformat(),
        'summary': {
            'paid_orders': paid_count,
            'revenue_cents': total_revenue,
            'revenue_display': money_display(total_revenue),
            'all_orders': Order.objects.count(),
        },
        'by_product_cents': by_product,
        'by_product_display': {k: money_display(v) for k, v in by_product.items()},
        'by_month_cents': dict(sorted(by_month.items())),
        'by_month_display': {k: money_display(v) for k, v in sorted(by_month.items())},
        'status_counts': by_status,
        'latest_payments': [
            {
                'payment_id': p.pk,
                'order_id': p.order_id,
                'gateway': p.gateway,
                'transaction_id': p.gateway_transaction_id,
                'amount_cents': p.amount_cents,
                'amount_display': money_display(p.amount_cents),
                'status': p.status,
                'created_at': p.created_at.isoformat(),
            }
            for p in payments
        ],
    }