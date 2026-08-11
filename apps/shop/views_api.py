"""REST API v1 — shared hub services for store operations.

Conventions (SOP):
  - Auth: X-API-Key header (sha256-hashed ApiKey records, or env API_KEY /
    SYSOP_API_KEY fallback). Roles: admin (full), sysop (read-only).
  - JSON body for POST/PUT. Money in integer cents. Timestamps ISO-8601.
  - Responses: success: true + data | success: false + error.
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import CartItem, Order, Payment, Product
from .services import (JsonError, build_cart, build_order, build_payment,
                       require_api_key)
from .store import (StoreError, add_to_cart, checkout, financial_report,
                    get_cart, remove_from_cart, set_quantity)


def _body(request):
    try:
        return json.loads(request.body or b'{}') or {}
    except json.JSONDecodeError:
        return {}


def _resolve_user(request):
    from django.contrib.auth import get_user_model
    data = _body(request)
    uid = data.get('user_id') or request.GET.get('user_id')
    if not uid:
        return None
    return get_user_model().objects.filter(pk=uid).first()


# ── Products ────────────────────────────────────────────────────────────────


@require_http_methods(['GET'])
@require_api_key(['sysop', 'admin'])
def api_products(request):
    products = Product.objects.filter(active=True)
    return JsonResponse({'success': True, 'data': [
        {
            'id': p.pk,
            'name': p.name,
            'description': p.description,
            'price_cents': p.price_cents,
            'price_display': p.price_display,
            'category': p.category,
        } for p in products
    ]})


# ── Cart ────────────────────────────────────────────────────────────────────


@require_http_methods(['GET'])
@require_api_key(['sysop', 'admin'])
def api_cart_get(request):
    user = _resolve_user(request)
    if not user:
        return JsonError('user_id is required (query param or request body).', 400)
    return JsonResponse({'success': True, 'data': build_cart(get_cart(user))})


@require_http_methods(['POST'])
@require_api_key(['admin'])
def api_cart_add(request):
    data = _body(request)
    user = _resolve_user(request)
    if not user:
        return JsonError('user_id is required in the request body.', 400)
    try:
        cart = add_to_cart(user, data.get('product_id'), data.get('quantity', 1))
    except ValueError as e:
        return JsonError(str(e), 400)
    return JsonResponse({'success': True, 'data': build_cart(cart)})


@require_http_methods(['POST'])
@require_api_key(['admin'])
def api_cart_remove(request):
    data = _body(request)
    user = _resolve_user(request)
    if not user:
        return JsonError('user_id is required in the request body.', 400)
    try:
        cart = remove_from_cart(user, data.get('item_id'))
    except ValueError as e:
        return JsonError(str(e), 400)
    return JsonResponse({'success': True, 'data': build_cart(cart)})


@require_http_methods(['POST'])
@require_api_key(['admin'])
def api_cart_set_qty(request):
    data = _body(request)
    user = _resolve_user(request)
    if not user:
        return JsonError('user_id is required in the request body.', 400)
    try:
        cart = set_quantity(user, data.get('item_id'), data.get('quantity', 0))
    except ValueError as e:
        return JsonError(str(e), 400)
    return JsonResponse({'success': True, 'data': build_cart(cart)})


# ── Checkout / orders / payments ─────────────────────────────────────────────


@require_http_methods(['POST'])
@require_api_key(['admin'])
def api_checkout(request):
    data = _body(request)
    user = _resolve_user(request)
    if not user:
        return JsonError('user_id is required in the request body.', 400)
    try:
        order, payment = checkout(
            user,
            card_token=data.get('card_token'),
            hub_ref=data.get('hub_ref'),
            payment_method=data.get('payment_method', 'card'),
        )
    except ValueError as e:
        return JsonError(str(e), 400)
    return JsonResponse({
        'success': True,
        'data': {
            'order': build_order(order),
            'payment': build_payment(payment),
        },
    })


@require_http_methods(['GET'])
@require_api_key(['sysop', 'admin'])
def api_orders(request):
    data = _body(request)
    user = _resolve_user(request)
    qs = Order.objects.all()
    if user:
        qs = qs.filter(user=user)
    status = data.get('status') or request.GET.get('status')
    if status:
        qs = qs.filter(status=status)
    qs = qs[:200]
    return JsonResponse({'success': True, 'data': [build_order(o) for o in qs]})


# ── Financial reporting ────────────────────────────────────────────────────────


@require_http_methods(['GET'])
@require_api_key(['admin'])
def api_financial(request):
    return JsonResponse({'success': True, 'data': financial_report()})


# ── Status ─────────────────────────────────────────────────────────────────────


@require_http_methods(['GET'])
@require_api_key(['sysop', 'admin'])
def api_health(request):
    from .services import service_health
    return JsonResponse({'success': True, 'data': service_health()})