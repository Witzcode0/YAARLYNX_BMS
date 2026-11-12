
from django.contrib import admin

from apps.marketplace.models import (
    Marketplace,
    CourierPartner,
    MarketplaceCourierPartner,
)


# ==========================================================
# COMMON ADMIN CONFIGURATION
# ==========================================================

ADMIN_READONLY_FIELDS = (
    "id",
    "created_at",
    "updated_at",
)


# ==========================================================
# MARKETPLACE COURIER INLINE
# ==========================================================

class MarketplaceCourierPartnerInline(admin.TabularInline):

    model = MarketplaceCourierPartner

    fk_name = "marketplace"

    extra = 1

    autocomplete_fields = ("courier_partner",)

    fields = (
        "courier_partner",
        "description",
        "is_active",
    )

    show_change_link = True


class CourierMarketplaceInline(admin.TabularInline):

    model = MarketplaceCourierPartner

    fk_name = "courier_partner"

    extra = 1

    autocomplete_fields = ("marketplace",)

    fields = (
        "marketplace",
        "description",
        "is_active",
    )

    show_change_link = True


# ==========================================================
# MARKETPLACE ADMIN
# ==========================================================

@admin.register(Marketplace)
class MarketplaceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "website",
        "courier_count",
        "is_active",
        "created_at",
    )

    list_display_links = (
        "name",
    )

    list_editable = (
        "is_active",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
        "website",
    )

    readonly_fields = ADMIN_READONLY_FIELDS

    inlines = (
        MarketplaceCourierPartnerInline,
    )

    date_hierarchy = "created_at"

    list_per_page = 25

    save_on_top = True

    fieldsets = (

        ("Marketplace Information", {
            "fields": (
                ("name", "code"),
                "website",
            ),
            "description": "Basic marketplace identification and website details."
        }),

        ("Additional Information", {
            "fields": (
                "description",
            ),
            "classes": ("collapse",),
        }),

        ("System Information", {
            "fields": (
                ("id", "is_active"),
                ("created_at", "updated_at"),
            ),
            "classes": ("collapse",),
        }),

    )

    @admin.display(description="Courier Partners")
    def courier_count(self, obj):
        return obj.courier_mappings.filter(
            is_active=True
        ).count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            "courier_mappings"
        )


# ==========================================================
# COURIER PARTNER ADMIN
# ==========================================================

@admin.register(CourierPartner)
class CourierPartnerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "contact_person_name",
        "contact_number",
        "city",
        "state",
        "marketplace_count",
        "is_active",
        "created_at",
    )

    list_display_links = (
        "name",
    )

    list_editable = (
        "is_active",
    )

    list_filter = (
        "is_active",
        "city",
        "state",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
        "contact_person_name",
        "designation",
        "contact_number",
        "alternate_contact_number",
        "email",
        "city",
        "state",
        "pincode",
    )

    readonly_fields = ADMIN_READONLY_FIELDS

    inlines = (
        CourierMarketplaceInline,
    )

    date_hierarchy = "created_at"

    list_per_page = 25

    save_on_top = True

    fieldsets = (

        ("Courier Partner Information", {
            "fields": (
                ("name", "code"),
            ),
            "description": "Basic courier company information."
        }),

        ("Contact Person Information", {
            "fields": (
                ("contact_person_name", "designation"),
                ("contact_number", "alternate_contact_number"),
                "email",
            ),
        }),

        ("Address Information", {
            "fields": (
                "address",
                ("city", "state"),
                "pincode",
            ),
            "classes": ("collapse",),
        }),

        ("Website & Tracking Information", {
            "fields": (
                ("website", "tracking_url"),
            ),
            "classes": ("collapse",),
        }),

        ("Additional Information", {
            "fields": (
                "description",
            ),
            "classes": ("collapse",),
        }),

        ("System Information", {
            "fields": (
                ("id", "is_active"),
                ("created_at", "updated_at"),
            ),
            "classes": ("collapse",),
        }),

    )

    @admin.display(description="Marketplaces")
    def marketplace_count(self, obj):
        return obj.marketplace_mappings.filter(
            is_active=True
        ).count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            "marketplace_mappings"
        )


# ==========================================================
# MARKETPLACE COURIER MAPPING ADMIN
# ==========================================================

@admin.register(MarketplaceCourierPartner)
class MarketplaceCourierPartnerAdmin(admin.ModelAdmin):

    list_display = (
        "marketplace",
        "courier_partner",
        "description",
        "is_active",
        "created_at",
    )

    list_display_links = (
        "marketplace",
    )

    list_editable = (
        "is_active",
    )

    list_filter = (
        "marketplace",
        "courier_partner",
        "is_active",
        "created_at",
    )

    search_fields = (
        "marketplace__name",
        "courier_partner__name",
        "description",
    )

    autocomplete_fields = (
        "marketplace",
        "courier_partner",
    )

    readonly_fields = ADMIN_READONLY_FIELDS

    date_hierarchy = "created_at"

    list_per_page = 25

    save_on_top = True

    fieldsets = (

        ("Marketplace & Courier Mapping", {
            "fields": (
                ("marketplace", "courier_partner"),
                "description",
                "is_active",
            ),
            "description": "Connect a marketplace with its courier partner."
        }),

        ("System Information", {
            "fields": (
                ("id", "created_at"),
                "updated_at",
            ),
            "classes": ("collapse",),
        }),

    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "marketplace",
            "courier_partner",
        )
