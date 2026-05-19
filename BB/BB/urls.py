<<<<<<< HEAD
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
=======
"""
URL configuration for BB project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('app.urls')),
    path('adpanel/',include('adpanel.urls')), 
    
]
from django.shortcuts import render


def error_page(request, code, message):
    return render(request, "error.html", {
        "code": code,
        "message": message
    })


def error_404(request, exception):
    return error_page(request, 404, "Page Not Found")


def error_403(request, exception):
    return error_page(request, 403, "Permission Denied")


def error_500(request):
    return error_page(request, 500, "Server Error")


handler404 = error_404
handler403 = error_403
handler500 = error_500

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Add testing routes to preview error pages locally
    urlpatterns += [
        path('404/', error_404, kwargs={'exception': Exception("Test")}),
        path('500/', error_500),
    ]

>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
