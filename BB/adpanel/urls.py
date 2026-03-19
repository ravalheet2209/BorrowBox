from django.urls import path
from . import views

app_name = "adpanel"

urlpatterns = [

    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("add-deposit/", views.add_deposit, name="add_deposit"),
    path("withdraw-deposit/", views.withdraw_deposit, name="withdraw_deposit"),

    path("owner-dashboard/", views.owner_dashboard, name="owner_dashboard"),

    path("my-items/", views.my_items, name="my_items"),
    path("add-item/", views.add_item, name="add_item"),
    path("edit-item/<int:id>/", views.edit_item, name="edit_item"),
    path("delete-item/<int:id>/", views.delete_item, name="delete_item"),

    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("admin-users/", views.admin_users, name="admin_users"),
    path("admin-user/<int:user_id>/", views.admin_user_detail, name="admin_user_detail"),

    path("admin-seller-requests/", views.admin_seller_requests, name="admin_seller_requests"),
    path("approve-seller/<int:user_id>/", views.approve_seller, name="approve_seller"),
    path("reject-seller/<int:user_id>/", views.reject_seller, name="reject_seller"),

    path("admin-categories/", views.admin_categories, name="admin_categories"),
    path("add-category/", views.add_category, name="add_category"),
    path("delete-category/<int:id>/", views.delete_category, name="delete_category"),

    path("admin-bookings/", views.admin_bookings, name="admin_bookings"),

    path("request-seller/", views.request_seller, name="request_seller"),

]