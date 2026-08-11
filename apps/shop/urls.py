from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views_api, views_mcp, views_pages

# Hub shared-services REST API (store operations)
api_patterns = [
    path('products', views_api.api_products),
    path('cart', views_api.api_cart_get),
    path('cart/add', views_api.api_cart_add),
    path('cart/remove', views_api.api_cart_remove),
    path('cart/set-quantity', views_api.api_cart_set_qty),
    path('checkout', csrf_exempt(views_api.api_checkout)),
    path('orders', views_api.api_orders),
    path('reports/financial', views_api.api_financial),
    path('health', views_api.api_health),
]

# MCP tool endpoints (hub operations manager)
mcp_patterns = [
    path('cart_status', views_mcp.mcp_status),
    path('checkout', csrf_exempt(views_mcp.mcp_checkout)),
    path('financial_check', views_mcp.mcp_financial),
    path('health_check', views_mcp.mcp_health),
]

# Store UI pages
page_patterns = [
    path('cart', views_pages.cart_view, name='cart'),
    path('cart/add', views_pages.cart_add),
    path('cart/remove/<int:item_id>', views_pages.cart_remove),
    path('cart/set-quantity/<int:item_id>', views_pages.cart_set_qty),
    path('checkout', views_pages.checkout_view, name='checkout'),
    path('orders', views_pages.orders_view, name='orders'),
    path('financial', views_pages.financial_view, name='financial'),
    path('health', views_pages.health_view, name='health'),
]