"""MCP endpoints — hub operations manager (OpenClaw/Hermes/human) access.

Convention (SOP): one POST/GET route per named tool at /mcp/<tool_name>.
Auth reuses the X-API-Key header and admin/sysop roles from the REST API.

Service surface for this store:
  - /mcp/cart_status      — read-only cart snapshot for a user (sysop/admin)
  - /mcp/checkout         — create an order and charge via hub gateway (admin)
  - /mcp/financial_check  — read-only revenue/orders report (admin)
  - /mcp/health_check     — service health + row counts (sysop/admin)
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Cart, Order, Payment, Product
from .services import JsonError, require_api_key
from .store import checkout, financial_report


def _success(data):
    return JsonResponse({'success': True, 'data': data})


def _error(message, status=400):
    return JsonResponse({'success': False, 'error': str(message)}, status=status)


@require_http_methods(['GET', 'POST'])
@require_api_key(['sysop', 'admin'])
def mcp_status(request):
    """Cart status for a user. GET /mcp/cart_status?user_id=N or POST with JSON body."""
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
    else:
        data = json_body(request)
        user_id = data.get('user_id')
    if not user_id:
        return _error('user_id is required.', 400)
    cart = Cart.objects.filter(user_id=user_id).first()
    if not cart:
        return _success({'user_id': int(user_id), 'cart': None, 'note': 'No cart exists yet.'})
    return _success({
        'user_id': int(user_id),
        'cart_id': cart.pk,
        'item_count': cart.item_count,
        'total_cents': cart.total_cents,
        'items': [
            {'product': it.product.name, 'quantity': it.quantity,
             'unit_cents': it.product.price_cents, 'subtotal_cents': it.subtotal_cents}
            for it in cart.items.select_related('product').all()
        ],
    })


@require_http_methods(['POST'])
@require_api_key(['admin'])
def mcp_checkout(request):
    """Create an order for user_id and charge via the hub gateway.

    Body: {user_id, [card_token], [hub_ref], [payment_method]}.
    """
    from django.contrib.auth import get_user_model
    data = json_body(request)
    user = get_user_model().objects.filter(pk=data.get('user_id')).first()
    if not user:
        return _error('Unknown user_id.', 400)
    try:
        order, payment = checkout(
            user,
            card_token=data.get('card_token'),
            hub_ref=data.get('hub_ref'),
            payment_method=data.get('payment_method', 'card'),
        )
    except ValueError as e:
        return _error(str(e), 400)
    return _success({
        'order_id': order.pk,
        'status': order.status,
        'total_cents': order.total_cents,
        'items': [{'name': i.name, 'quantity': i.quantity, 'price_cents': i.price_cents} for i in order.items.all()],
        'payment': {
            'payment_id': payment.pk,
            'gateway': payment.gateway,
            'transaction_id': payment.gateway_transaction_id,
            'status': payment.status,
            'amount_cents': payment.amount_cents,
        },
    })


@require_http_methods(['GET'])
@require_api_key(['admin'])
def mcp_financial(request):
    """Read-only financial report: revenue, orders by status, by month, by product."""
    return _success(financial_report())


@require_http_methods(['GET'])
@require_api_key(['sysop', 'admin'])
def mcp_health(request):
    """Health + row counts for the store service — identical payload to
    /api/v1/health, so business manager and sysops get one status source."""
    from .services import service_health
    return _success(service_health())


def json_body(request):
    import json as _json
    try:
        return _json.loads(request.body or b'{}') or {}
    except _json.JSONDecodeError:
        return {}