from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.shop.urls import api_patterns, mcp_patterns, page_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
    path('api/v1/', include((api_patterns, 'shop_api'), namespace='shop_api')),
    path('mcp/', include((mcp_patterns, 'shop_mcp'), namespace='shop_mcp')),
    path('auth/', include('apps.authentication.urls')),
    path('', include((page_patterns, 'shop_pages'), namespace='shop_pages')),
    path('', include('apps.party_pages.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
