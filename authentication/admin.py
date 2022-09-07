import imp
from django.contrib import admin
from . models import CustomUser, PaymentMethod, PaymentDetails, CustomUserPortfolio

admin.site.register(CustomUser)

admin.site.register(PaymentMethod)

admin.site.register(PaymentDetails)

admin.site.register(CustomUserPortfolio)

# Register your models here.
