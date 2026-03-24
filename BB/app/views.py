from decimal import ROUND_HALF_UP, Decimal
from django.db import models
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator


from .models import User, Contact, Item, Category, Booking, Review

from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q


    # Create your views here.
def home(request):
        featured_items = Item.objects.all().order_by('-id')[:6]
        categories = Category.objects.annotate(item_count=models.Count('items'))

        hero_items = []
        
        if request.user.is_authenticated:
            last_booking = Booking.objects.filter(user=request.user).order_by('-created_at').first()
            if last_booking:
                hero_items.append({
                    'item': last_booking.item,
                    'title': "Recently Rented"
                })
                # Top suggestions from same category
                if last_booking.item.category:
                    suggestions = Item.objects.filter(category=last_booking.item.category).exclude(id=last_booking.item.id).order_by('?')[:2]
                    for sugg in suggestions:
                        hero_items.append({
                            'item': sugg,
                            'title': "Top Suggestion"
                        })
        
        # Fill the rest with random top suggestions if we don't have enough
        if len(hero_items) < 3:
            needed = 3 - len(hero_items)
            exclude_ids = [hi['item'].id for hi in hero_items]
            random_items = Item.objects.exclude(id__in=exclude_ids).order_by('?')[:needed]
            for ri in random_items:
                hero_items.append({
                    'item': ri,
                    'title': "Top Suggestion"
                })

        return render(request, 'home.html', {
            'featured_items': featured_items,
            'categories': categories,
            'hero_items': hero_items,
        })

    

def contacts(request):  
        return render(request, 'contacts.html')



def item_listing(request):
        items = Item.objects.select_related('category', 'owner').all().order_by('-id')
        categories = Category.objects.annotate(item_count=models.Count('items'))

        search_query = request.GET.get('q')
        category_id = request.GET.get('category')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price') 
        availability = request.GET.get('availability')

        # 🔍 SEARCH (Title, Description, Category, Location)
        if search_query:
            items = items.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(category__name__icontains=search_query)  
            )

        # 📂 Category filter
        if category_id:
            items = items.filter(category_id=category_id)

        # 💰 Price filter
        if min_price:
            items = items.filter(price_per_day__gte=min_price)

        if max_price:
            items = items.filter(price_per_day__lte=max_price)

        # 📦 Availability filter (kept safe)
        if availability == "available":
            items = items.filter(is_available=True)
        elif availability == "rented":
            items = items.filter(is_available=False)

        paginator = Paginator(items, 9)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'item_listing.html', {
            'items': page_obj,
            'categories': categories,
            'search_query': search_query  # optional but useful
        })
    
        
def delogin(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')   # redirect to home

        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'login.html')
def register(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.first_name = name
        user.save()

        return redirect('/login/')

    return render(request, 'register.html')
def logout_user(request):
    logout(request)
    return redirect('/')


def single_item(request):  
        return render(request, 'single_item.html')

def blog(request):  
        return render(request, 'blog.html')

def blog_grid(request):  
        return render(request, 'blog_grid.html')

def contact(request):
    if request.method == "POST":
            first_name = request.POST["first_name"]
            last_name  = request.POST["last_name"]
            email      = request.POST["email"]
            phone      = request.POST["phone"]
            subject    = request.POST["subject"]
            message    = request.POST["message"]    
            Contact.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            return redirect('/contact/')
            return render(request, 'contact.html')

def item_detail(request, id):
        item = get_object_or_404(Item, id=id)

        return render(request, "item_detail.html", {"item": item})




    # Auto expire pending bookings
def expire_old_bookings():
    now = timezone.now()
    # Expire pending bookings over 15 minutes
    Booking.objects.filter(
        status="pending",
        expires_at__lt=now
    ).update(status="expired")
    
    # Mark confirmed rentals as completed if their end date has passed
    Booking.objects.filter(
        status="confirmed",
        end_date__lt=now.date()
    ).update(status="completed")

    # Check availability
def check_availability(item, start_date, end_date):

        expire_old_bookings()

        return not Booking.objects.filter(
            item=item,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).filter(
            Q(status="confirmed") |
            Q(status="pending", expires_at__gt=timezone.now())
        ).exists()



    # Product detail page
def product_detail(request, id):
        expire_old_bookings()
        item = get_object_or_404(Item, id=id)
        has_past_booking = False
        if request.user.is_authenticated:
            # Consider any confirmed/expired booking as a past booking
            has_past_booking = Booking.objects.filter(
                item=item, 
                user=request.user,
                status__in=['confirmed', 'expired']
            ).exists()
        return render(request, "product.html", {"item": item, "has_past_booking": has_past_booking})

@login_required
def add_review(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)
        rating = request.POST.get("rating", 5)
        comment = request.POST.get("comment", "")
        
        has_past_booking = Booking.objects.filter(
            item=item, 
            user=request.user,
            status__in=['confirmed', 'expired']
        ).exists()
        
        if has_past_booking and comment:
            Review.objects.create(
                item=item,
                user=request.user,
                rating=int(rating),
                comment=comment
            )
    return redirect("product", id=item_id)



    # Get blocked dates (AJAX)
def get_booked_dates(request, item_id):

        item = get_object_or_404(Item, id=item_id)

        bookings = item.bookings.filter(
           Q(status="confirmed") |
            Q(status="pending", expires_at__gt=timezone.now())
        )

        data = []
        for booking in bookings:
            data.append({
                "start": booking.start_date.strftime("%Y-%m-%d"),
                "end": booking.end_date.strftime("%Y-%m-%d"),
            })

        return JsonResponse(data, safe=False)

    # Add to cart (create pending booking)
@login_required
def add_to_cart(request, item_id):

        if request.method == "POST":

            item = get_object_or_404(Item, id=item_id)

            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")

            if not start_date or not end_date:
                return redirect("product", id=item.id)

            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            days = (end_date - start_date).days
            total_price = days * item.price_per_day

            if not check_availability(item, start_date, end_date):
                return redirect("product", id=item.id)

            Booking.objects.create(
                item=item,
                user=request.user,
                start_date=start_date,
                end_date=end_date,
                total_price=total_price,
                status="pending"
            )

            return redirect("cart")

        return redirect("product", id=item_id)

    # Cart page
@login_required
def cart(request):
    expire_old_bookings()
    bookings = Booking.objects.filter(user=request.user, status="pending")

    subtotal = sum(booking.total_price for booking in bookings)

    service_fee = (Decimal("0.02") * Decimal(subtotal)).quantize(Decimal("0.01"),
    rounding=ROUND_HALF_UP ) # 2% service fee
    total = Decimal(subtotal) + service_fee
    
    # Check deposit requirements
    new_rentals_count = bookings.count()
    active_rentals = Booking.objects.filter(user=request.user, status="confirmed").count()
    total_rentals = active_rentals + new_rentals_count
    required_deposit = total_rentals * 2000
    current_deposit = request.user.profile.security_deposit if hasattr(request.user, 'profile') else Decimal("0.00")
    deficit = Decimal(required_deposit) - Decimal(current_deposit)
    needs_deposit = deficit > 0
    
    # Check ID proof
    needs_id_proof = not request.user.profile.id_proof

    context = {
        "bookings": bookings,
        "subtotal": subtotal,
        "service_fee": service_fee,
        "total": total,
        "required_deposit": required_deposit,
        "current_deposit": current_deposit,
        "deficit": deficit,
        "needs_deposit": needs_deposit,
        "needs_id_proof": needs_id_proof
    }

    return render(request, "cart.html", context)


def remove(request, booking_id):
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=request.user,
            status="pending"
        )
        booking.status = "cancelled"
        booking.save()
        
        return redirect("cart")



from django.contrib import messages

@login_required
def checkout(request):

    profile = request.user.profile
    if not profile.id_proof:
        messages.error(request, "Please upload your ID proof in your profile before renting.")
        return redirect("adpanel:profile")

    now = timezone.now()

    expire_old_bookings()

    # Pending bookings to confirm
    pending_bookings = Booking.objects.filter(
        user=request.user,
        status="pending",
        expires_at__gt=now
    )
    
    new_rentals_count = pending_bookings.count()
    if new_rentals_count > 0:
        active_rentals = Booking.objects.filter(user=request.user, status="confirmed").count()
        total_rentals = active_rentals + new_rentals_count
        required_deposit = total_rentals * 2000

        if float(profile.security_deposit) < required_deposit:
            messages.error(request, f"Insufficient security deposit. You need {required_deposit} for {total_rentals} items but have {profile.security_deposit}. Please add more deposit.")
            return redirect("adpanel:dashboard")

        # Confirm bookings
        pending_bookings.update(status="confirmed")
        messages.success(request, f"Successfully booked {new_rentals_count} item(s)!")
        return redirect("adpanel:dashboard")

    return redirect("cart")
      
@login_required
def payment_success(request):
        return render(request, "payment_success.html")
def faq(request):  
        return render(request, 'faq.html')

def about(request):  
        return render(request, 'about.html')
