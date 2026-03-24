from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver


# =====================================================
# CONTACT
# =====================================================

class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# =====================================================
# CATEGORY
# =====================================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# =====================================================
# ITEM
# =====================================================

class Item(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="items"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='items/')
    image2 = models.ImageField(upload_to='items/', blank=True, null=True)
    image3 = models.ImageField(upload_to='items/', blank=True, null=True)
    image4 = models.ImageField(upload_to='items/', blank=True, null=True)
    image5 = models.ImageField(upload_to='items/', blank=True, null=True)

    @property
    def rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return None

    def __str__(self):
        return self.title


# =====================================================
# BOOKING
# =====================================================

class Booking(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    start_date = models.DateField()
    end_date = models.DateField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Set expiry time only for pending bookings
        if self.status == "pending" and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.title} ({self.status})"


# =====================================================
# REVIEW
# =====================================================

class Review(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.item.title}"



# =====================================================
# PROFILE
# =====================================================

class Profile(models.Model):

    SELLER_STATUS_CHOICES = (
        ('none', 'Not Seller'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_seller = models.BooleanField(default=False)

    seller_status = models.CharField(
        max_length=20,
        choices=SELLER_STATUS_CHOICES,
        default='none'
    )

    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    id_number = models.CharField(max_length=50, blank=True, null=True)
    id_proof = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def mask_id_number(self):
        if self.id_number and len(self.id_number) > 4:
            return '*' * (len(self.id_number) - 4) + self.id_number[-4:]
        return self.id_number

    def __str__(self):
        return self.user.username


# =====================================================
# AUTO CREATE PROFILE
# =====================================================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()