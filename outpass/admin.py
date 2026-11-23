from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import OutpassRequest, MovementLog

admin.site.register(OutpassRequest)
admin.site.register(MovementLog)
