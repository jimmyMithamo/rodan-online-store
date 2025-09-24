from django.contrib import admin
from .models import User as CustomUser
# Register your models here.
admin.site.register(CustomUser)
