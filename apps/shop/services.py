"""Shop plumbing: API key auth, shared journal services, hub gateway, serializers."""

import hashlib
import os
import secrets
import time

import requests
from django.utils import timezone

from .models import ApiKey, Order, Payment, Product, Cart

VERSION = '1.0.0'
APP_STARTED = time.time()


def uptime_seconds():
    return int(time.time() - APP_STARTED)


def service_health():
    """Single source of truth for service status — served by /api/v1/health,
    /mcp/health_check and the /health sysop page. Business managers and sysops
    query any surface: identical payload."""
    cfg = hub_gateway_config()
    gateway_mode = {
        'mode': 'hub' if (cfg['url'] and cfg['api_key']) else 'simulated',
        'url': cfg['url'] or None,
        'note': None if (cfg['url'] and cfg['api_key']) else 'HUB_GATEWAY_URL/API_KEY unset — charges simulated.',
    }
    status_counts = {}
    for status, _label in Order.STATUSES:
        status_counts[status] = Order.objects.filter(status=status).count()
    last_payment = Payment.objects.order_by('-created_at').first()
    return {
        'service': 'advance-shop',
        'version': VERSION,
        'integration': 'hub-shared-services',
        'host': os.uname().nodename,
        'status': 'ok',
        'checked_at': timezone.now().isoformat(),
        'uptime_seconds': uptime_seconds(),
        'gateway': gateway_mode,
        'row_counts': {
            'products': Product.objects.count(),
            'carts': Cart.objects.count(),
            'orders': Order.objects.count(),
            'payments': Payment.objects.count(),
        },
        'order_status_counts': status_counts,
        'last_payment': build_payment(last_payment) if last_payment else None,
    }


def hash_key(key):
    """SHA-256 hash of an API key — DB leak yields no working keys."""
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def _env_role(key):
    if key and key == os.getenv('API_KEY', '').strip():
        return ApiKey.ROLE_ADMIN
    if key and key == os.getenv('SYSOP_API_KEY', '').strip():
        return ApiKey.ROLE_SYSOP
    return None


def lookup_role(api_key):
    """Resolve an API key to a role. DB first (hashed), env-var fallback."""
    if not api_key:
        return None
    try:
        record = ApiKey.objects.filter(key_hash=hash_key(api_key), active=True).first()
        if record and record.role:
            return record.role
    except Exception:
        pass
    return _env_role(api_key)


def require_api_key(allowed_roles):
    """Decorator: require an X-API-Key header with one of the allowed roles."""
    def decorator(view):
        def wrapped(request, *args, **kwargs):
            api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
            if not api_key:
                return JsonError('Missing X-API-Key header.', 401)
            role = lookup_role(api_key)
            if role is None:
                return JsonError('Invalid API key.', 401)
            if role not in allowed_roles:
                return JsonError(
                    'API key role "%s" does not have permission for this endpoint. Requires one of: %s'
                    % (role, ', '.join(allowed_roles)), 403)
            request.api_role = role
            request.api_key_authenticated = True
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


# ── Helpers / serializers ────────────────────────────────────────────────


def money_display(cents):
    return f'${(cents or 0) / 100:,.2f}'


def JsonError(message, status):
    from django.http import JsonResponse
    return JsonResponse({'success': False, 'error': message}, status=status)


def build_cart(cart):
    return {
        'cart_id': cart.pk,
        'user_id': cart.user_id,
        'item_count': cart.item_count,
        'total': {'cents': cart.total_cents, 'display': money_display(cart.total_cents)},
        'items': [
            {
                'id': item.pk,
                'product_id': item.product_id,
                'name': item.product.name,
                'price_cents': item.product.price_cents,
                'quantity': item.quantity,
                'subtotal_cents': item.subtotal_cents,
            }
            for item in cart.items.select_related('product').all()
        ],
    }


def build_order(order):
    return {
        'order_id': order.pk,
        'user_id': order.user_id,
        'status': order.status,
        'total': {'cents': order.total_cents, 'display': order.total_display},
        'payment_method': order.payment_method,
        'created_at': order.created_at.isoformat(),
        'paid_at': order.paid_at.isoformat() if order.paid_at else None,
        'items': [
            {
                'name': item.name,
                'price_cents': item.price_cents,
                'quantity': item.quantity,
                'subtotal_cents': item.subtotal_cents,
            }
            for item in order.items.all()
        ],
    }


def build_payment(payment):
    return {
        'payment_id': payment.pk,
        'order_id': payment.order_id,
        'gateway': payment.gateway,
        'gateway_transaction_id': payment.gateway_transaction_id,
        'amount_cents': payment.amount_cents,
        'amount_display': money_display(payment.amount_cents),
        'status': payment.status,
        'created_at': payment.created_at.isoformat(),
    }


# ------------------------------------------------------------------ Hub gateway


class HubGatewayError(Exception):
    pass


def hub_gateway_config():
    """Hub payment gateway connection settings (env-driven, shared hub)."""
    return {
        'url': os.getenv('HUB_GATEWAY_URL', '').strip(),
        'api_key': os.getenv('HUB_GATEWAY_API_KEY', '').strip(),
        'simulate': os.getenv('HUB_GATEWAY_SIMULATE', '1') in ('1', 'true', 'yes'),
    }


def charge_via_hub(order, amount_cents, card_token=None, hub_ref=None):
    """Route a charge through the Hub Payment Gateway.

    Returns a dict like {"gateway": "hub"|"test", "transaction_id": "...",
    "status": "succeeded"|"failed", "raw": {...}}.

    When the hub URL/API key are not configured, falls back to the local
    test gateway simulation so development keeps working off-line.
    """
    cfg = hub_gateway_config()

    if cfg['url'] and cfg['api_key']:
        try:
            resp = requests.post(
                cfg['url'].rstrip('/') + '/v1/charges',
                headers={
                    'Authorization': 'Bearer ' + cfg['api_key'],
                    'Content-Type': 'application/json',
                },
                json={
                    'order_id': order.pk,
                    'amount_cents': amount_cents,
                    'currency': 'CAD',
                    'card_token': card_token,
                    'hub_ref': hub_ref,
                    'meta': {
                        'source': 'advance-party',
                        'user_id': order.user_id,
                    },
                },
                timeout=15,
            )
            payload = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
            if resp.status_code >= 400:
                raise HubGatewayError(payload or {'hub_error': resp.status_code})
            txn = payload.get('transaction_id') or payload.get('id') or str(order.pk)
            status = 'succeeded' if payload.get('status') in ('succeeded', 'paid', 'success', 'captured') else 'failed'
            return {'gateway': 'hub', 'transaction_id': txn, 'status': status, 'raw': payload}
        except HubGatewayError:
            raise
        except requests.RequestException as e:
            raise HubGatewayError(f'Hub gateway unreachable: {e}')

    # Test-gateway simulation (dev default)
    return {
        'gateway': 'test',
        'transaction_id': 'sim_' + (hub_ref or '') + str(order.pk) + secrets.token_hex(4),
        'status': 'succeeded',
        'raw': {'simulated': True, 'note': 'HUB_GATEWAY_URL not configured — test simulation used.'},
    }


# ------------------------------------------------------------------ journal style helpers


def cents_total(queryset, field='total_cents'):
    total = 0
    for row in queryset:
        total += getattr(row, field) or 0
    return total