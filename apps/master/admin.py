from django.contrib import admin
from apps.master.models import *

# Register your models here.
@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "short_name",
        "is_active",
    )

    search_fields = (
        "name",
        "short_name",
    )

    list_filter = (
        "is_active",
    )