from .models import Booking
from django.utils import timezone

def cart_status(request):
    """
    Makes cart_count available in all templates.
    Only counts pending bookings that haven't expired.
    """
    if request.user.is_authenticated:
        now = timezone.now()
        count = Booking.objects.filter(
            user=request.user, 
            status="pending",
            expires_at__gt=now
        ).count()
        return {'cart_count': count}
    return {'cart_count': 0}

def razorpay_key(request):
    from django.conf import settings
    return {'razorpay_key_id': settings.RAZORPAY_KEY_ID}
