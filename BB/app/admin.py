from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Contact)
admin.site.register(Item)
admin.site.register(Category)
admin.site.register(Booking)

