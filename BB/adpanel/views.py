from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
<<<<<<< HEAD
from django.db.models import Sum, Count
from app.models import Booking, Item, Category, Profile, WithdrawalRequest
from django.contrib.auth.models import User
from app.emails import send_deposit_email
from decimal import Decimal

# =====================================================
# DECORATORS
# =====================================================

def admin_required(function):
    return user_passes_test(lambda u: u.is_superuser)(function)

def seller_required(function):
    return user_passes_test(lambda u: u.profile.seller_status == 'approved')(function)


# =====================================================
# USER DASHBOARD
=======
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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
# =====================================================

@login_required
def dashboard(request):
<<<<<<< HEAD
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    rental_history = Booking.objects.filter(user=request.user).select_related('item', 'item__category').order_by('-created_at')
    
    active_rentals = rental_history.filter(status__in=['pending', 'confirmed']).count()
    total_rented = rental_history.count()
    total_spend = rental_history.aggregate(total=Sum('total_price'))['total'] or 0
    
    most_category = rental_history.values('item__category__name').annotate(count=Count('item__category')).order_by('-count').first()
    
    deposit_balance = profile.security_deposit
    required_deposit = active_rentals * 2000
    
    return render(request, "dashboard_home.html", {
        "rental_history": rental_history,
        "active_rentals": active_rentals,
        "total_rented": total_rented,
        "total_spend": total_spend,
        "most_category": most_category,
        "deposit_balance": deposit_balance,
        "required_deposit": required_deposit,
    })


@login_required
def profile(request):
    p, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        u = request.user
        
        u.first_name = request.POST.get("first_name", u.first_name)
        u.email = request.POST.get("email", u.email)
        u.save()
        
        p.phone = request.POST.get("phone", p.phone)
        p.address = request.POST.get("address", p.address)
        p.id_number = request.POST.get("id_number", p.id_number)
        
        if 'id_proof' in request.FILES:
            p.id_proof = request.FILES['id_proof']
            
        p.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("adpanel:profile")
        
    return render(request, "profile.html")
=======
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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d


@login_required
def add_deposit(request):
<<<<<<< HEAD
    if request.method == "POST":
        amount = Decimal(request.POST.get("amount", 0))
        if amount > 0:
            request.user.profile.security_deposit += amount
            request.user.profile.save()
            send_deposit_email(request.user, amount, "add", request.user.profile.security_deposit)
            messages.success(request, f"₹{amount} added to your security deposit.")
    return redirect("adpanel:dashboard")


@login_required
def withdraw_deposit(request):
    if request.method == "POST":
        amount = Decimal(request.POST.get("amount", 0))
        current = request.user.profile.security_deposit
        
        # Check buffer
        active_rentals = Booking.objects.filter(user=request.user, status__in=['pending', 'confirmed']).count()
        required = active_rentals * 2000
        
        if amount <= (current - required):
            request.user.profile.security_deposit -= amount
            request.user.profile.save()
            send_deposit_email(request.user, amount, "withdraw", request.user.profile.security_deposit)
            messages.success(request, f"₹{amount} withdrawal initiated.")
        else:
            messages.error(request, "Insufficient available balance (must keep buffer for active rentals).")
            
=======
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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
    return redirect("adpanel:dashboard")


# =====================================================
<<<<<<< HEAD
# SELLER / OWNER
=======
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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
# =====================================================

@login_required
def request_seller(request):
<<<<<<< HEAD
    p, _ = Profile.objects.get_or_create(user=request.user)
    if p.seller_status == 'none' or p.seller_status == 'rejected':
        p.seller_status = 'pending'
        p.save()
        messages.success(request, "Seller request submitted!")
    return redirect("adpanel:profile")


@login_required
@seller_required
def owner_dashboard(request):
    my_items = Item.objects.filter(owner=request.user)
    bookings = Booking.objects.filter(item__owner=request.user).select_related('item', 'user').order_by('-created_at')

    active_orders = bookings.filter(status__in=['pending', 'confirmed']).count()
    total_earnings = bookings.aggregate(total=Sum('total_price'))['total'] or 0

    # Wallet / withdrawal
    profile, _ = Profile.objects.get_or_create(user=request.user)
    wallet_balance = profile.wallet_balance
    withdrawal_history = WithdrawalRequest.objects.filter(seller=request.user).order_by('-requested_at')[:10]

    return render(request, "owner_dashboard.html", {
        "total_items": my_items.count(),
        "total_bookings": bookings.count(),
        "bookings": bookings[:10],
        "active_orders": active_orders,
        "total_earnings": total_earnings,
        "wallet_balance": wallet_balance,
        "withdrawal_history": withdrawal_history,
=======

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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
    })


@login_required
<<<<<<< HEAD
@seller_required
def confirm_return(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, item__owner=request.user)
    if booking.status == 'confirmed':
        booking.status = 'completed'
        booking.seller_confirmed = True
        booking.save()
        # Credit the earned amount to seller's wallet
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.wallet_balance += booking.total_price
        profile.save()
        messages.success(
            request,
            f"Booking for {booking.item.title} marked as returned. "
            f"₹{booking.total_price} credited to your wallet."
        )
    else:
        messages.error(request, "This booking cannot be marked as returned.")
    return redirect("adpanel:owner_dashboard")

@login_required
@seller_required
def withdraw_earnings(request):
    """Seller requests a withdrawal from their wallet balance."""
    if request.method != "POST":
        return redirect("adpanel:owner_dashboard")

    profile, _ = Profile.objects.get_or_create(user=request.user)
    try:
        amount = Decimal(request.POST.get("amount", "0"))
    except Exception:
        messages.error(request, "Invalid amount.")
        return redirect("adpanel:owner_dashboard")

    upi_id = request.POST.get("upi_id", "").strip()
    bank_account = request.POST.get("bank_account", "").strip()

    if amount <= 0:
        messages.error(request, "Withdrawal amount must be greater than zero.")
        return redirect("adpanel:owner_dashboard")

    if amount > profile.wallet_balance:
        messages.error(
            request,
            f"Insufficient wallet balance. Available: ₹{profile.wallet_balance}"
        )
        return redirect("adpanel:owner_dashboard")

    if not upi_id and not bank_account:
        messages.error(request, "Please provide a UPI ID or bank account number.")
        return redirect("adpanel:owner_dashboard")

    # Deduct from wallet and record request
    profile.wallet_balance -= amount
    profile.save()

    WithdrawalRequest.objects.create(
        seller=request.user,
        amount=amount,
        upi_id=upi_id or None,
        bank_account=bank_account or None,
        status='pending',
    )

    messages.success(
        request,
        f"₹{amount} withdrawal request submitted successfully! "
        "It will be processed within 2–3 business days."
    )
    return redirect("adpanel:owner_dashboard")


@login_required
@seller_required
def my_items(request):
    items = Item.objects.filter(owner=request.user).select_related('category')
    return render(request, "my_items.html", {"items": items})


@login_required
@seller_required
def add_item(request):
    if request.method == "POST":
        category = get_object_or_404(Category, id=request.POST.get("category"))
        new_item = Item.objects.create(
            owner=request.user,
            category=category,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            price_per_day=request.POST.get("price_per_day"),
            location=request.POST.get("location"),
            image=request.FILES.get("image"),
        )
        for field in ['image2', 'image3', 'image4', 'image5']:
            if field in request.FILES:
                setattr(new_item, field, request.FILES[field])
        new_item.save()
        messages.success(request, "Item added successfully!")
        return redirect("adpanel:my_items")
        
    categories = Category.objects.all()
    return render(request, "add_item.html", {"categories": categories})


@login_required
@seller_required
def edit_item(request, id):
    item = get_object_or_404(Item, id=id, owner=request.user)
    if request.method == "POST":
        item.category = get_object_or_404(Category, id=request.POST.get("category"))
        item.title = request.POST.get("title")
        item.description = request.POST.get("description")
        item.price_per_day = request.POST.get("price_per_day")
        item.location = request.POST.get("location")
        
        for field in ['image', 'image2', 'image3', 'image4', 'image5']:
            if field in request.FILES:
                setattr(item, field, request.FILES[field])
        
        item.save()
        messages.success(request, "Item updated!")
        return redirect("adpanel:my_items")
        
    categories = Category.objects.all()
    return render(request, "edit_item.html", {"item": item, "categories": categories})


@login_required
@seller_required
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, owner=request.user)
    item.delete()
    messages.success(request, "Item deleted.")
=======
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

>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
    return redirect("adpanel:my_items")


# =====================================================
<<<<<<< HEAD
# ADMIN
# =====================================================

@login_required
@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_items = Item.objects.count()
    total_bookings = Booking.objects.count()
    pending_sellers = Profile.objects.filter(seller_status='pending').count()
    
    return render(request, "admin_dashboard.html", {
        "total_users": total_users,
        "total_items": total_items,
        "total_bookings": total_bookings,
        "pending_sellers_count": pending_sellers,
    })


@login_required
@admin_required
def admin_users(request):
    users = User.objects.all()
    return render(request, "admin_users.html", {"users": users})


@login_required
@admin_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    user_bookings = Booking.objects.filter(user=user).order_by('-created_at')
    total_rented = user_bookings.count()
    active_rentals = user_bookings.filter(status__in=['pending', 'confirmed']).count()
    total_spent = user_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    
    user_items = Item.objects.filter(owner=user)
    seller_bookings = Booking.objects.filter(item__owner=user)
    total_earnings = seller_bookings.aggregate(total=Sum('total_price'))['total'] or 0
    
    return render(request, "admin_user_detail.html", {
        "user_obj": user,
        "user_bookings": user_bookings,
        "total_rented": total_rented,
        "active_rentals": active_rentals,
        "total_spent": total_spent,
        "total_items_listed": user_items.count(),
        "total_earnings": total_earnings,
    })


@login_required
@admin_required
def admin_seller_requests(request):
    pending_profiles = Profile.objects.filter(seller_status='pending')
    return render(request, "admin_seller_requests.html", {"pending_profiles": pending_profiles})


@login_required
@admin_required
def approve_seller(request, user_id):
    p = get_object_or_404(Profile, user_id=user_id)
    p.seller_status = 'approved'
    p.is_seller = True
    p.save()
    messages.success(request, f"User {p.user.username} approved as seller.")
    return redirect("adpanel:admin_seller_requests")


@login_required
@admin_required
def reject_seller(request, user_id):
    p = get_object_or_404(Profile, user_id=user_id)
    p.seller_status = 'rejected'
    p.save()
    messages.warning(request, f"User {p.user.username} seller request rejected.")
    return redirect("adpanel:admin_seller_requests")


@login_required
@admin_required
def admin_categories(request):
    categories = Category.objects.all()
    return render(request, "admin_categories.html", {"categories": categories})


@login_required
@admin_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")
        if name:
            Category.objects.create(name=name, image=image)
            messages.success(request, "Category added.")
    return redirect("adpanel:admin_categories")


@login_required
@admin_required
def delete_category(request, id):
    cat = get_object_or_404(Category, id=id)
    cat.delete()
    messages.success(request, "Category deleted.")
    return redirect("adpanel:admin_categories")


@login_required
@admin_required
def admin_bookings(request):
    bookings = Booking.objects.select_related('item', 'user', 'item__owner').all().order_by('-created_at')
    return render(request, "admin_bookings.html", {"bookings": bookings})
=======
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
>>>>>>> 8c1d6ca0f454a5d5de0fcab3349b39eb5c153d5d
