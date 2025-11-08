# clasificador/admin.py
from django.contrib import admin
from .models import EspeciePlanta, MiPlanta, MonitoreoPlanta, ConsejoCuidado

# Register your models here.
admin.site.register(EspeciePlanta)
admin.site.register(MiPlanta)
admin.site.register(MonitoreoPlanta)
admin.site.register(ConsejoCuidado)