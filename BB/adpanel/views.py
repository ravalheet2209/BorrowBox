from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
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
# =====================================================

@login_required
def dashboard(request):
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


@login_required
def add_deposit(request):
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
            
    return redirect("adpanel:dashboard")


# =====================================================
# SELLER / OWNER
# =====================================================

@login_required
def request_seller(request):
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
    })


@login_required
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
    return redirect("adpanel:my_items")


# =====================================================
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
