from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from app.models import Item, Category, Profile, Booking
from app.views import expire_old_bookings


# =====================================================
# ACCESS CONTROL HELPERS
# =====================================================

def seller_required(user):
    return user.is_authenticated and user.profile.seller_status == "approved"


def admin_required(user):
    return user.is_authenticated and user.is_superuser


# =====================================================
# USER DASHBOARD (RENT ANALYTICS)
# =====================================================

@login_required
def dashboard(request):
    expire_old_bookings()
    user = request.user

    bookings = Booking.objects.filter(user=user).select_related(
        "item",
        "item__category"
    )

    total_rented = bookings.count()

    active_rentals = bookings.filter(
        status="confirmed"
    ).count()

    total_spend = bookings.aggregate(
        Sum("total_price")
    )["total_price__sum"] or 0

    most_category = (
        bookings.values("item__category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
        .first()
    )

    rental_history = bookings.order_by("-created_at")

    deposit_balance = user.profile.security_deposit

    context = {
        "total_rented": total_rented,
        "active_rentals": active_rentals,
        "total_spend": total_spend,
        "most_category": most_category,
        "rental_history": rental_history,
        "deposit_balance": deposit_balance,
        "required_deposit": active_rentals * 2000,
    }

    return render(request, "dashboard_home.html", context)


@login_required
def add_deposit(request):
    next_url = request.POST.get("next") or request.GET.get("next") or "adpanel:dashboard"
    if request.method == "POST":
        amount = request.POST.get("amount")
        try:
            amount = float(amount)
            if amount > 0:
                profile = request.user.profile
                profile.security_deposit = float(profile.security_deposit) + amount
                profile.save()
                messages.success(request, f"Successfully added {amount} to security deposit.")
        except ValueError:
            messages.error(request, "Invalid amount.")
            
    if next_url.startswith('/'):
        return redirect(next_url)
    return redirect(next_url)

@login_required
def withdraw_deposit(request):
    expire_old_bookings()
    if request.method == "POST":
        amount = request.POST.get("amount")
        try:
            amount = float(amount)
            profile = request.user.profile
            # Check required deposit
            active_rentals = Booking.objects.filter(user=request.user, status="confirmed").count()
            required_deposit = active_rentals * 2000
            if amount > 0 and (float(profile.security_deposit) - amount) >= required_deposit:
                profile.security_deposit = float(profile.security_deposit) - amount
                profile.save()
                messages.success(request, f"Successfully withdrew {amount} from security deposit.")
            else:
                messages.error(request, f"Cannot withdraw. You need at least {required_deposit} for active rentals.")
        except ValueError:
            messages.error(request, "Invalid amount.")
    return redirect("adpanel:dashboard")


# =====================================================
# SELLER DASHBOARD (EARNINGS)
# =====================================================

@login_required
@user_passes_test(seller_required)
def owner_dashboard(request):

    items = Item.objects.filter(owner=request.user)

    bookings = Booking.objects.filter(
        item__owner=request.user
    ).select_related("item", "user", "user__profile").order_by("-created_at")

    total_items = items.count()

    total_bookings = bookings.count()

    total_earnings = bookings.aggregate(
        Sum("total_price")
    )["total_price__sum"] or 0

    active_orders = bookings.filter(
        status="confirmed"
    ).count()

    context = {
        "total_items": total_items,
        "total_bookings": total_bookings,
        "total_earnings": total_earnings,
        "active_orders": active_orders,
        "bookings": bookings,
    }

    return render(request, "owner_dashboard.html", context)


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):

    total_users = User.objects.count()

    total_items = Item.objects.count()

    total_categories = Category.objects.count()

    pending_sellers = Profile.objects.filter(
        seller_status="pending"
    ).count()

    total_bookings = Booking.objects.count()

    total_revenue = Booking.objects.aggregate(
        Sum("total_price")
    )["total_price__sum"] or 0

    context = {
        "total_users": total_users,
        "total_items": total_items,
        "total_categories": total_categories,
        "pending_sellers": pending_sellers,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
    }

    return render(request, "admin_dashboard.html", context)


# =====================================================
# ADMIN USER MANAGEMENT
# =====================================================

@login_required
@user_passes_test(admin_required)
def admin_users(request):

    users = User.objects.all().order_by("-date_joined")

    return render(request, "admin_users.html", {
        "users": users
    })


@login_required
@user_passes_test(admin_required)
def admin_user_detail(request, user_id):

    user = get_object_or_404(User, id=user_id)

    # Seller Data
    items_listed = Item.objects.filter(owner=user)

    seller_bookings = Booking.objects.filter(
        item__owner=user
    )

    total_items_listed = items_listed.count()

    total_earnings = seller_bookings.aggregate(
        Sum("total_price")
    )["total_price__sum"] or 0

    # Renter Data
    user_bookings = Booking.objects.filter(user=user)

    total_rented = user_bookings.count()

    total_spent = user_bookings.aggregate(
        Sum("total_price")
    )["total_price__sum"] or 0

    active_rentals = user_bookings.filter(
        status="confirmed"
    ).count()

    context = {
        "user_obj": user,
        "items_listed": items_listed,
        "seller_bookings": seller_bookings,
        "total_items_listed": total_items_listed,
        "total_earnings": total_earnings,
        "total_rented": total_rented,
        "total_spent": total_spent,
        "active_rentals": active_rentals,
        "user_bookings": user_bookings,
    }

    return render(request, "admin_user_detail.html", context)


# =====================================================
# PROFILE
# =====================================================

@login_required
def profile(request):

    if request.method == "POST":

        user = request.user
        profile = user.profile

        user.first_name = request.POST.get("first_name")
        user.email = request.POST.get("email")
        profile.phone = request.POST.get("phone")
        profile.address = request.POST.get("address")

        if request.POST.get("id_number"):
            profile.id_number = request.POST.get("id_number")

        if request.FILES.get("id_proof"):
            profile.id_proof = request.FILES.get("id_proof")

        user.save()
        profile.save()

        messages.success(request, "Profile updated successfully!")

        return redirect("adpanel:profile")

    return render(request, "profile.html")


# =====================================================
# SELLER REQUEST
# =====================================================

@login_required
def request_seller(request):

    profile = request.user.profile

    if profile.seller_status in ["none", "rejected"]:

        profile.seller_status = "pending"

        profile.save()

        messages.success(request, "Seller request submitted!")

    return redirect("adpanel:profile")


# =====================================================
# ADMIN SELLER APPROVAL
# =====================================================

@login_required
@user_passes_test(admin_required)
def admin_seller_requests(request):

    pending_profiles = Profile.objects.filter(
        seller_status="pending"
    )

    return render(request, "admin_seller_requests.html", {
        "pending_profiles": pending_profiles
    })


@login_required
@user_passes_test(admin_required)
def approve_seller(request, user_id):

    profile = get_object_or_404(Profile, user__id=user_id)

    profile.seller_status = "approved"

    profile.is_seller = True

    profile.save()

    messages.success(request, "Seller approved")

    return redirect("adpanel:admin_seller_requests")


@login_required
@user_passes_test(admin_required)
def reject_seller(request, user_id):

    profile = get_object_or_404(Profile, user__id=user_id)

    profile.seller_status = "rejected"

    profile.is_seller = False

    profile.save()

    messages.warning(request, "Seller rejected")

    return redirect("adpanel:admin_seller_requests")


# =====================================================
# CATEGORY MANAGEMENT
# =====================================================

@login_required
@user_passes_test(admin_required)
def admin_categories(request):

    categories = Category.objects.all()

    return render(request, "admin_categories.html", {
        "categories": categories
    })


@login_required
@user_passes_test(admin_required)
def add_category(request):

    if request.method == "POST":

        name = request.POST.get("name")

        if name:

            Category.objects.create(name=name)

            messages.success(request, "Category added successfully!")

    return redirect("adpanel:admin_categories")


@login_required
@user_passes_test(admin_required)
def delete_category(request, id):

    category = get_object_or_404(Category, id=id)

    category.delete()

    messages.success(request, "Category deleted!")

    return redirect("adpanel:admin_categories")


# =====================================================
# ITEM MANAGEMENT (SELLER)
# =====================================================

@login_required
@user_passes_test(seller_required)
def my_items(request):

    items = Item.objects.filter(owner=request.user)

    return render(request, "my_items.html", {
        "items": items
    })


@login_required
@user_passes_test(seller_required)
def add_item(request):

    categories = Category.objects.all()

    if request.method == "POST":

        Item.objects.create(
            owner=request.user,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            category=Category.objects.get(
                id=request.POST.get("category")
            ),
            price_per_day=request.POST.get("price_per_day"),
            location=request.POST.get("location"),
            image=request.FILES.get("image"),
            image2=request.FILES.get("image2"),
            image3=request.FILES.get("image3"),
            image4=request.FILES.get("image4"),
            image5=request.FILES.get("image5"),
        )

        messages.success(request, "Item added successfully!")

        return redirect("adpanel:my_items")

    return render(request, "add_item.html", {
        "categories": categories
    })


@login_required
@user_passes_test(seller_required)
def edit_item(request, id):

    item = get_object_or_404(
        Item,
        id=id,
        owner=request.user
    )

    categories = Category.objects.all()

    if request.method == "POST":

        item.title = request.POST.get("title")

        item.description = request.POST.get("description")

        item.price_per_day = request.POST.get("price_per_day")

        item.location = request.POST.get("location")

        item.category = Category.objects.get(
            id=request.POST.get("category")
        )

        if request.FILES.get("image"):
            item.image = request.FILES.get("image")
        if request.FILES.get("image2"):
            item.image2 = request.FILES.get("image2")
        if request.FILES.get("image3"):
            item.image3 = request.FILES.get("image3")
        if request.FILES.get("image4"):
            item.image4 = request.FILES.get("image4")
        if request.FILES.get("image5"):
            item.image5 = request.FILES.get("image5")

        item.save()

        messages.success(request, "Item updated successfully!")

        return redirect("adpanel:my_items")

    return render(request, "edit_item.html", {
        "item": item,
        "categories": categories
    })


@login_required
@user_passes_test(seller_required)
def delete_item(request, id):

    item = get_object_or_404(
        Item,
        id=id,
        owner=request.user
    )

    item.delete()

    messages.success(request, "Item deleted successfully!")

    return redirect("adpanel:my_items")


# =====================================================
# ADMIN BOOKING PANEL
# =====================================================

@login_required
@user_passes_test(admin_required)
def admin_bookings(request):

    bookings = Booking.objects.select_related(
        "user",
        "item",
        "item__owner"
    ).order_by("-created_at")

    return render(request, "admin_bookings.html", {
        "bookings": bookings
    })