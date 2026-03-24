from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    
    path('', views.home, name='home'),
    path('contacts/', views.contacts, name='contacts'),
    path('item_listing/', views.item_listing, name='item_listing'),
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    path('product/<int:id>/', views.product_detail, name='product'),
    path("get-booked-dates/<int:item_id>/", views.get_booked_dates, name="get_booked_dates"),
    path("add-to-cart/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path("add-review/<int:item_id>/", views.add_review, name="add_review"),
    path("remove/<int:booking_id>/", views.remove, name="remove"),
   
    path('cart/', views.cart, name='cart'),

    path("checkout/", views.checkout, name="checkout"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path('login/', views.delogin, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_user, name='logout'),
   
    path('single_item/', views.single_item, name='single_item'),
    path('blog/', views.blog, name='blog'),
    path('blog_grid/', views.blog_grid, name='blog_grid'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
]   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)