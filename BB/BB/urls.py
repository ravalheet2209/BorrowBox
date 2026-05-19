from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found, server_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('accounts/', include('allauth.urls')),
    path('adpanel/', include(('adpanel.urls', 'adpanel'), namespace='adpanel')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'app.views.custom_404'
handler500 = 'app.views.custom_500'
