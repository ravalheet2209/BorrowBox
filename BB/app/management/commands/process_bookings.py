from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Booking, Profile
from app.emails import (
    send_expiring_soon_email, 
    send_overdue_reminder_email, 
    send_fine_applied_email
)
from decimal import Decimal

class Command(BaseCommand):
    help = 'Processes expiring bookings, sends reminders, and applies late fines.'

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        
        # 1. Expiring Soon Notification (Today is the end date)
        expiring_soon = Booking.objects.filter(
            status='confirmed',
            end_date=today,
            is_expiring_soon_sent=False,
            seller_confirmed=False
        )
        for booking in expiring_soon:
            send_expiring_soon_email(booking)
            booking.is_expiring_soon_sent = True
            booking.save()
            self.stdout.write(self.style.SUCCESS(f'Sent expiring soon email for booking {booking.id}'))

        # 2. Overdue Bookings (Date is over & not confirmed by seller)
        overdue_bookings = Booking.objects.filter(
            status='confirmed',
            end_date__lt=today,
            seller_confirmed=False
        )

        for booking in overdue_bookings:
            # End date's theoretical expiry at end of day (23:59:59)
            # Actually, if date is less than today, it's already overdue.
            # Let's say it's overdue at midnight of the next day.
            expiry_datetime = timezone.make_aware(
                timezone.datetime.combine(booking.end_date + timedelta(days=1), timezone.datetime.min.time())
            )
            
            hours_overdue = (now - expiry_datetime).total_seconds() / 3600

            # --- Reminder logic every 2 hours ---
            if hours_overdue > 0:
                last_reminder = booking.last_reminder_sent_at
                if not last_reminder or (now - last_reminder).total_seconds() >= 7200: # 2 hours
                    send_overdue_reminder_email(booking)
                    booking.last_reminder_sent_at = now
                    booking.save()
                    self.stdout.write(self.style.SUCCESS(f'Sent overdue reminder for booking {booking.id}'))

            # --- Fine logic: > 12 hours overdue, 200 Rs every 2 hours ---
            if hours_overdue > 12:
                last_fine = booking.last_fine_applied_at
                if not last_fine or (now - last_fine).total_seconds() >= 7200: # 2 hours
                    fine_amount = Decimal('200.00')
                    
                    buyer_profile = booking.user.profile
                    seller_profile = booking.item.owner.profile
                    
                    if buyer_profile.security_deposit >= fine_amount:
                        buyer_profile.security_deposit -= fine_amount
                        seller_profile.security_deposit += fine_amount
                        buyer_profile.save()
                        seller_profile.save()
                        
                        booking.total_fines += fine_amount
                        booking.last_fine_applied_at = now
                        booking.save()
                        
                        send_fine_applied_email(booking, fine_amount)
                        self.stdout.write(self.style.WARNING(f'Applied 200 Rs fine for booking {booking.id}'))
                    else:
                        # Handle case where buyer has 0 deposit left (optional)
                        self.stdout.write(self.style.ERROR(f'Buyer {booking.user.username} has insufficient funds for fine on booking {booking.id}'))

        self.stdout.write("Booking processing complete.")
