from django.contrib import admin
from apps.pdf_overlay.models import OverlayImage
# Register your models here.
@admin.register(OverlayImage)
class OverlayImageAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "is_default",
        "created_at",
    )

    list_filter = (
        "is_default",
    )

    search_fields = (
        "name",
    )

    readonly_fields = (
        "created_at",
    )