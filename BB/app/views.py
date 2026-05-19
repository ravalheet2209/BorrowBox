from decimal import ROUND_HALF_UP, Decimal
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.contrib.auth.models import User
from .models import Booking, Category, Contact, Item, Review, Profile
from .emails import send_booking_buyer_email, send_booking_seller_email



# =====================================================
# HELPERS
# =====================================================

def expire_old_bookings():
    """Expire pending bookings older than 15 min. Confirmed bookings are completed manually by the seller."""
    now = timezone.now()
    Booking.objects.filter(
        status="pending",
        expires_at__lt=now
    ).update(status="expired")


def check_availability(item, start_date, end_date):
    """Return True if the item is available for the given date range."""
    expire_old_bookings()
    return not Booking.objects.filter(
        item=item,
        start_date__lte=end_date,
        end_date__gte=start_date,
    ).filter(
        Q(status="confirmed") |
        Q(status="pending", expires_at__gt=timezone.now())
    ).exists()


# =====================================================
# PUBLIC PAGES
# =====================================================

def home(request):
    featured_items = Item.objects.all().order_by('?')[:4]
    categories = Category.objects.annotate(item_count=Count('items'))

    hero_items = []

    if request.user.is_authenticated:
        last_booking = Booking.objects.filter(
            user=request.user
        ).select_related('item', 'item__category').order_by('-created_at').first()

        if last_booking:
            hero_items.append({
                'item': last_booking.item,
                'title': "Recently Rented",
            })
            if last_booking.item.category:
                suggestions = Item.objects.filter(
                    category=last_booking.item.category
                ).exclude(id=last_booking.item.id).order_by('?')[:2]
                for suggestion in suggestions:
                    hero_items.append({'item': suggestion, 'title': "Top Suggestion"})

    # Fill remaining slots with random items
    if len(hero_items) < 3:
        needed = 3 - len(hero_items)
        exclude_ids = [entry['item'].id for entry in hero_items]
        random_items = Item.objects.select_related('category').exclude(id__in=exclude_ids).order_by('?')[:needed]
        for item in random_items:
            hero_items.append({'item': item, 'title': "Top Suggestion"})

    return render(request, 'home.html', {
        'featured_items': featured_items,
        'categories': categories,
        'hero_items': hero_items,
    })


def item_listing(request):
    items = Item.objects.select_related('category', 'owner').all().order_by('title')
    categories = Category.objects.annotate(item_count=Count('items'))

    search_query = request.GET.get('q')
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    location = request.GET.get('location')
    sort_by = request.GET.get('sort')

    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if category_id:
        items = items.filter(category_id=category_id)

    if min_price:
        items = items.filter(price_per_day__gte=min_price)

    if max_price:
        items = items.filter(price_per_day__lte=max_price)

    if location:
        items = items.filter(location__icontains=location)

    if sort_by == 'low':
        items = items.order_by('price_per_day')
    elif sort_by == 'high':
        items = items.order_by('-price_per_day')
    elif sort_by == 'new':
        items = items.order_by('-id')

    paginator = Paginator(items, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'item_listing.html', {
        'items': page_obj,
        'categories': categories,
        'search_query': search_query,
    })


def item_detail(request, id):
    item = get_object_or_404(Item.objects.select_related('category', 'owner'), id=id)
    return render(request, "item_detail.html", {"item": item})


def product_detail(request, id):
    expire_old_bookings()
    item = get_object_or_404(Item.objects.select_related('category', 'owner'), id=id)

    has_past_booking = False
    if request.user.is_authenticated:
        has_past_booking = Booking.objects.filter(
            item=item,
            user=request.user,
            status__in=['confirmed', 'expired'],
        ).exists()

    return render(request, "product.html", {
        "item": item,
        "has_past_booking": has_past_booking,
    })


def contact(request):
    if request.method == "POST":
        Contact.objects.create(
            first_name=request.POST.get("first_name", ""),
            last_name=request.POST.get("last_name", ""),
            email=request.POST.get("email", ""),
            phone=request.POST.get("phone", ""),
            subject=request.POST.get("subject", ""),
            message=request.POST.get("message", ""),
        )
        messages.success(request, "Thanks! Your message has been sent. We'll get back to you within 24 hours.")
        return redirect('contact')

    return render(request, 'contact.html')


def about(request):
    return render(request, 'about.html')


def faq(request):
    return render(request, 'faq.html')


def how_it_works(request):
    return render(request, 'how_it_works.html')


def careers(request):
    return render(request, 'careers.html')


def terms(request):
    return render(request, 'terms.html')


def privacy(request):
    return render(request, 'privacy.html')


def cookies(request):
    return render(request, 'cookies.html')


def insurance(request):
    return render(request, 'insurance.html')


def trust(request):
    return render(request, 'trust.html')


# Stub views (kept for URL routing)
def contacts(request):
    return redirect('contact')

def single_item(request):
    return redirect('item_listing')

def blog(request):
    return render(request, 'blog.html')

def blog_grid(request):
    return render(request, 'blog.html')


# =====================================================
# AUTH
# =====================================================

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')

        return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')


from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

def register(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'register.html', {'error': e.messages[0]})

        user = User.objects.create_user(
            username=request.POST.get('username'),
            email=request.POST.get('email'),
            password=password,
        )
        user.first_name = request.POST.get('name')
        user.save()
        return redirect('/login/')

    return render(request, 'register.html')


def logout_user(request):
    logout(request)
    return redirect('/')


# =====================================================
# BOOKING / CART
# =====================================================

def get_booked_dates(request, item_id):
    """AJAX endpoint: returns blocked date ranges for an item."""
    item = get_object_or_404(Item, id=item_id)
    bookings = item.bookings.filter(
        Q(status="confirmed") |
        Q(status="pending", expires_at__gt=timezone.now())
    )
    data = [
        {
            "start": b.start_date.strftime("%Y-%m-%d"), 
            "end": (b.end_date + timezone.timedelta(days=1)).strftime("%Y-%m-%d"),
            "status": b.status
        }
        for b in bookings
    ]
    return JsonResponse(data, safe=False)


@login_required
def add_to_cart(request, item_id):
    """Create a pending booking (add item to cart)."""
    if request.method != "POST":
        return redirect("product", id=item_id)

    item = get_object_or_404(Item, id=item_id)
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    if not start_date or not end_date:
        return redirect("product", id=item.id)

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    if not check_availability(item, start_date, end_date):
        return redirect("product", id=item.id)

    days = (end_date - start_date).days + 1
    total_price = days * item.price_per_day

    Booking.objects.create(
        item=item,
        user=request.user,
        start_date=start_date,
        end_date=end_date,
        total_price=total_price,
        status="pending",
        expires_at=timezone.now() + timezone.timedelta(minutes=15)
    )
    return redirect("cart")


@login_required
def cart(request):
    expire_old_bookings()
    bookings = Booking.objects.filter(user=request.user, status="pending").select_related('item')

    subtotal = sum(b.total_price for b in bookings)
    service_fee = (Decimal("0.02") * Decimal(subtotal)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total = Decimal(subtotal) + service_fee

    # Deposit requirement
    active_rentals = Booking.objects.filter(user=request.user, status="confirmed").count()
    total_rentals = active_rentals + bookings.count()
    required_deposit = total_rentals * 2000

    profile = request.user.profile
    current_deposit = profile.security_deposit if hasattr(request.user, 'profile') else Decimal("0.00")
    deficit = Decimal(required_deposit) - Decimal(current_deposit)

    return render(request, "cart.html", {
        "bookings": bookings,
        "subtotal": subtotal,
        "service_fee": service_fee,
        "total": total,
        "required_deposit": required_deposit,
        "current_deposit": current_deposit,
        "deficit": deficit,
        "needs_deposit": deficit > 0,
        "needs_id_proof": not profile.id_proof,
    })


@login_required
def remove_from_cart(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status="pending")
    booking.status = "cancelled"
    booking.save()
    return redirect("cart")


@login_required
def checkout(request):
    profile = request.user.profile

    if not profile.id_proof:
        messages.error(request, "Please upload your ID proof in your profile before renting.")
        return redirect("adpanel:profile")

    expire_old_bookings()

    pending_bookings = Booking.objects.filter(
        user=request.user,
        status="pending",
        expires_at__gt=timezone.now(),
    ).select_related('item', 'item__owner')

    if not pending_bookings.exists():
        return redirect("cart")

    active_rentals = Booking.objects.filter(user=request.user, status="confirmed").count()
    total_rentals = active_rentals + pending_bookings.count()
    required_deposit = total_rentals * 2000

    if float(profile.security_deposit) < required_deposit:
        messages.error(
            request,
            f"Insufficient security deposit. You need ₹{required_deposit} for "
            f"{total_rentals} item(s) but have ₹{profile.security_deposit}. "
            "Please add more deposit."
        )
        return redirect("adpanel:dashboard")

    booking_count = pending_bookings.count()
    
    # Send emails for each confirmed booking
    for booking in pending_bookings:
        send_booking_buyer_email(booking, request.user, booking.item.owner)
        send_booking_seller_email(booking, request.user, booking.item.owner)
        
    pending_bookings.update(status="confirmed")
    messages.success(request, f"Successfully booked {booking_count} item(s)!")
    return redirect("adpanel:dashboard")


@login_required
def payment_success(request):
    return render(request, "payment_success.html")


# =====================================================
# REVIEWS
# =====================================================

@login_required
def add_review(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)

        has_past_booking = Booking.objects.filter(
            item=item,
            user=request.user,
            status__in=['confirmed', 'expired'],
        ).exists()

        comment = request.POST.get("comment", "")
        if has_past_booking and comment:
            Review.objects.create(
                item=item,
                user=request.user,
                rating=int(request.POST.get("rating", 5)),
                comment=comment,
            )

    return redirect("product", id=item_id)


# =====================================================
# ERROR HANDLERS
# =====================================================

def custom_404(request, exception=None):
    """Custom 404 Page Not Found handler."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 Server Error handler."""
    return render(request, '500.html', status=500)
