from django.urls import path
<<<<<<< HEAD
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('item_listing/', views.item_listing, name='item_listing'),
    path('item/<int:id>/', views.item_detail, name='item_detail'),
    path('product/<int:id>/', views.product_detail, name='product'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_user, name='logout'),
    
    # Booking / Cart
    path('get-booked-dates/<int:item_id>/', views.get_booked_dates, name='get_booked_dates'),
    path('add-to-cart/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove-from-cart/<int:booking_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    
    # Reviews
    path('add-review/<int:item_id>/', views.add_review, name='add_review'),
    
    # Extra pages (footer links)
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('careers/', views.careers, name='careers'),
    path('blog/', views.blog, name='blog'),
    path('trust/', views.trust, name='trust'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('cookies/', views.cookies, name='cookies'),
    path('insurance/', views.insurance, name='insurance'),

    # Stub / Legacy URLs
    path('contacts/', views.contacts, name='contacts'),
    path('single-item/', views.single_item, name='single_item'),
    path('blog-grid/', views.blog_grid, name='blog_grid'),
]
=======

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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
