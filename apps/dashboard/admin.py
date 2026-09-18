from decimal import Decimal

from django import forms
from django.contrib import admin
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils.html import format_html

from .models import (
    Party,
    PartyPaymentQR,
    PaymentMethod,
    PartyOrder,
    Payment,
)


# =========================================================
# COMMON HELPERS
# =========================================================

def currency_html(amount, color=None, strong=True):
    """
    Safely format Decimal currency for Django Admin.

    Important:
    Django 6.1 can raise:
        ValueError: Unknown format code 'f' for object of type 'SafeString'

    Therefore the numeric formatting is performed BEFORE
    passing the value into format_html().
    """

    amount = amount or Decimal("0.00")

    try:
        amount = Decimal(str(amount))
    except Exception:
        amount = Decimal("0.00")

    formatted_amount = f"{amount:,.2f}"

    if strong and color:
        return format_html(
            '<strong style="color:{};">₹{}</strong>',
            color,
            formatted_amount,
        )

    if strong:
        return format_html(
            "<strong>₹{}</strong>",
            formatted_amount,
        )

    if color:
        return format_html(
            '<span style="color:{};">₹{}</span>',
            color,
            formatted_amount,
        )

    return format_html(
        "₹{}",
        formatted_amount,
    )


# =========================================================
# COMMON ADMIN ACTIONS
# =========================================================

@admin.action(description="Activate selected records")
def activate_records(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)

    modeladmin.message_user(
        request,
        f"{updated} record(s) activated successfully.",
    )


@admin.action(description="Deactivate selected records")
def deactivate_records(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)

    modeladmin.message_user(
        request,
        f"{updated} record(s) deactivated successfully.",
    )


# =========================================================
# PARTY ADMIN FORM
# =========================================================

class PartyAdminForm(forms.ModelForm):

    class Meta:
        model = Party
        fields = "__all__"

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter party / supplier name",
                }
            ),
            "contact_person": forms.TextInput(
                attrs={
                    "placeholder": "Enter contact person name",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Enter primary phone number",
                }
            ),
            "alternate_phone": forms.TextInput(
                attrs={
                    "placeholder": "Enter alternate phone number",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter email address",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "placeholder": "Enter complete address",
                    "rows": 3,
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "Enter city",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "placeholder": "Enter state",
                }
            ),
            "pincode": forms.TextInput(
                attrs={
                    "placeholder": "Enter pincode",
                }
            ),
            "gpay_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter G-Pay number (optional)",
                }
            ),
            "gst_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter GST number",
                }
            ),
            "bank_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter bank name",
                }
            ),
            "account_holder_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter account holder name",
                }
            ),
            "account_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter account number",
                }
            ),
            "ifsc_code": forms.TextInput(
                attrs={
                    "placeholder": "Enter IFSC code",
                }
            ),
            "branch_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter branch name",
                }
            ),
            "upi_id": forms.TextInput(
                attrs={
                    "placeholder": "Enter UPI ID",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "placeholder": "Enter additional notes",
                    "rows": 4,
                }
            ),
        }

    def clean_name(self):
        value = self.cleaned_data.get("name", "")

        value = " ".join(
            value.strip().split()
        )

        if not value:
            raise forms.ValidationError(
                "Party name is required."
            )

        return value

    def clean_email(self):
        value = self.cleaned_data.get(
            "email",
            "",
        )

        return value.strip().lower()

    def clean_phone(self):
        return self.cleaned_data.get(
            "phone",
            "",
        ).strip()

    def clean_alternate_phone(self):
        return self.cleaned_data.get(
            "alternate_phone",
            "",
        ).strip()

    def clean_gpay_number(self):
        return self.cleaned_data.get(
            "gpay_number",
            "",
        ).strip()

    def clean_gst_number(self):
        value = self.cleaned_data.get(
            "gst_number",
            "",
        ).strip().upper()

        if value and len(value) != 15:
            raise forms.ValidationError(
                "GST number must contain exactly 15 characters."
            )

        return value

    def clean_ifsc_code(self):
        return self.cleaned_data.get(
            "ifsc_code",
            "",
        ).strip().upper()

    def clean_upi_id(self):
        return self.cleaned_data.get(
            "upi_id",
            "",
        ).strip().lower()


# =========================================================
# PARTY PAYMENT QR FORM
# =========================================================

class PartyPaymentQRAdminForm(forms.ModelForm):

    class Meta:
        model = PartyPaymentQR
        fields = "__all__"

        widgets = {
            "qr_name": forms.TextInput(
                attrs={
                    "placeholder": "Example: G-Pay QR",
                }
            ),
            "upi_id": forms.TextInput(
                attrs={
                    "placeholder": "Example: name@okaxis",
                }
            ),
        }

    def clean_qr_name(self):
        value = self.cleaned_data.get(
            "qr_name",
            "",
        )

        value = " ".join(
            value.strip().split()
        )

        if not value:
            raise forms.ValidationError(
                "QR name is required."
            )

        return value

    def clean_upi_id(self):
        return self.cleaned_data.get(
            "upi_id",
            "",
        ).strip().lower()


# =========================================================
# PARTY PAYMENT QR INLINE
# =========================================================

class PartyPaymentQRInline(admin.TabularInline):

    model = PartyPaymentQR
    form = PartyPaymentQRAdminForm

    extra = 1
    min_num = 0

    fields = (
        "qr_preview",
        "qr_name",
        "qr_image",
        "upi_id",
        "is_primary",
        "is_active",
    )

    readonly_fields = (
        "qr_preview",
    )

    show_change_link = True

    verbose_name = "Payment QR"
    verbose_name_plural = "Payment QR Codes"

    @admin.display(description="Preview")
    def qr_preview(self, obj):

        if obj and obj.pk and obj.qr_image:

            return format_html(
                """
                <div style="
                    width:80px;
                    height:80px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    background:#ffffff;
                    border:1px solid #e5e7eb;
                    border-radius:10px;
                    padding:5px;
                ">
                    <img
                        src="{}"
                        alt="QR"
                        style="
                            max-width:70px;
                            max-height:70px;
                            object-fit:contain;
                            border-radius:5px;
                        "
                    >
                </div>
                """,
                obj.qr_image.url,
            )

        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "No QR",
        )


# =========================================================
# PAYMENT INLINE
# =========================================================

class PaymentInline(admin.TabularInline):

    model = Payment

    extra = 0

    fields = (
        "payment_number",
        "payment_date",
        "payment_method",
        "amount",
        "status",
        "transaction_reference",
        "is_active",
    )

    readonly_fields = (
        "payment_number",
    )

    autocomplete_fields = (
        "payment_method",
    )

    show_change_link = True

    verbose_name = "Payment"
    verbose_name_plural = "Payments"

    ordering = (
        "-payment_date",
        "-created_at",
    )


# =========================================================
# PARTY ADMIN
# =========================================================

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):

    form = PartyAdminForm

    inlines = (
        PartyPaymentQRInline,
    )

    list_display = (
        "party_display",
        "party_type_display",
        "contact_display",
        "phone_display",
        "gst_display",
        "bank_display",
        "qr_count_display",
        "status_display",
        "created_display",
    )

    search_fields = (
        "id",
        "name",
        "contact_person",
        "phone",
        "alternate_phone",
        "email",
        "gst_number",
        "gpay_number",
        "bank_name",
        "account_holder_name",
        "account_number",
        "ifsc_code",
        "upi_id",
        "city",
        "state",
        "pincode",
    )

    list_filter = (
        "party_type",
        "is_active",
        "state",
        "city",
        "created_at",
        "updated_at",
    )

    ordering = (
        "name",
    )

    date_hierarchy = "created_at"

    list_per_page = 25

    actions = (
        activate_records,
        deactivate_records,
    )

    readonly_fields = (
        "id",
        "qr_summary",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Party Information",
            {
                "fields": (
                    "id",
                    "name",
                    "party_type",
                    "contact_person",
                    "is_active",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "phone",
                    "alternate_phone",
                    "email",
                    "gpay_number",
                )
            },
        ),
        (
            "Address",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "address",
                    "city",
                    "state",
                    "pincode",
                )
            },
        ),
        (
            "GST Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "gst_number",
                )
            },
        ),
        (
            "Bank Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number",
                    "ifsc_code",
                    "branch_name",
                    "upi_id",
                )
            },
        ),
        (
            "Payment QR Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "qr_summary",
                )
            },
        ),
        (
            "Additional Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "notes",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @transaction.atomic
    def save_formset(
        self,
        request,
        form,
        formset,
        change,
    ):

        instances = formset.save(
            commit=False
        )

        deleted_objects = formset.deleted_objects

        for instance in instances:

            if isinstance(
                instance,
                PartyPaymentQR,
            ):
                instance.party = form.instance

            instance.save()

        for obj in deleted_objects:
            obj.delete()

        formset.save_m2m()

        # -----------------------------------------------------
        # ONLY ONE PRIMARY QR PER PARTY
        # -----------------------------------------------------

        primary_qrs = (
            PartyPaymentQR.objects
            .filter(
                party=form.instance,
                is_primary=True,
            )
            .order_by(
                "-created_at",
                "-pk",
            )
        )

        primary_qr = primary_qrs.first()

        if primary_qr:

            primary_qrs.exclude(
                pk=primary_qr.pk
            ).update(
                is_primary=False
            )

    @admin.display(
        description="Party",
        ordering="name",
    )
    def party_display(self, obj):

        return format_html(
            """
            <div>
                <strong style="
                    color:#153030;
                    font-size:13px;
                ">
                    {}
                </strong>

                <div style="
                    color:#9ca3af;
                    font-size:10px;
                    margin-top:2px;
                ">
                    ID: {}
                </div>
            </div>
            """,
            obj.name,
            str(obj.id)[:8],
        )

    @admin.display(
        description="Type",
        ordering="party_type",
    )
    def party_type_display(self, obj):

        return format_html(
            """
            <span style="
                display:inline-block;
                padding:4px 9px;
                border-radius:999px;
                background:#f1f5f9;
                color:#334155;
                font-size:11px;
                font-weight:600;
            ">
                {}
            </span>
            """,
            obj.get_party_type_display(),
        )

    @admin.display(
        description="Contact",
    )
    def contact_display(self, obj):

        if not obj.contact_person:

            return format_html(
                '<span style="color:#9ca3af;">{}</span>',
                "—",
            )

        return format_html(
            """
            <div>
                <strong>{}</strong>

                <div style="
                    color:#9ca3af;
                    font-size:11px;
                    margin-top:2px;
                ">
                    {}
                </div>
            </div>
            """,
            obj.contact_person,
            obj.email or "No email",
        )

    @admin.display(
        description="Phone",
    )
    def phone_display(self, obj):

        if not obj.phone:

            return format_html(
                '<span style="color:#9ca3af;">{}</span>',
                "—",
            )

        return obj.phone

    @admin.display(
        description="GST",
    )
    def gst_display(self, obj):

        if not obj.gst_number:

            return format_html(
                '<span style="color:#9ca3af;">{}</span>',
                "Not Provided",
            )

        return format_html(
            """
            <span style="
                font-family:monospace;
                font-size:11px;
                font-weight:600;
                color:#153030;
            ">
                {}
            </span>
            """,
            obj.gst_number,
        )

    @admin.display(
        description="Bank",
    )
    def bank_display(self, obj):

        if not obj.bank_name:

            return format_html(
                '<span style="color:#9ca3af;">{}</span>',
                "Not Provided",
            )

        return format_html(
            """
            <div>
                <strong>{}</strong>

                <div style="
                    color:#9ca3af;
                    font-size:10px;
                    margin-top:2px;
                ">
                    {}
                </div>
            </div>
            """,
            obj.bank_name,
            obj.ifsc_code or "IFSC not provided",
        )

    @admin.display(
        description="QR Codes",
    )
    def qr_count_display(self, obj):

        count = obj.payment_qrs.count()

        if count == 0:

            return format_html(
                '<span style="color:#9ca3af;">{}</span>',
                "No QR",
            )

        return format_html(
            """
            <span style="
                display:inline-block;
                padding:4px 9px;
                border-radius:999px;
                background:#ecfdf5;
                color:#047857;
                font-size:11px;
                font-weight:700;
            ">
                {} QR
            </span>
            """,
            count,
        )

    @admin.display(
        description="Status",
        ordering="is_active",
    )
    def status_display(self, obj):

        if obj.is_active:

            return format_html(
                """
                <span style="
                    display:inline-block;
                    padding:4px 9px;
                    border-radius:999px;
                    background:#ecfdf5;
                    color:#047857;
                    font-size:11px;
                    font-weight:700;
                ">
                    {}
                </span>
                """,
                "Active",
            )

        return format_html(
            """
            <span style="
                display:inline-block;
                padding:4px 9px;
                border-radius:999px;
                background:#fef2f2;
                color:#b91c1c;
                font-size:11px;
                font-weight:700;
            ">
                {}
            </span>
            """,
            "Inactive",
        )

    @admin.display(
        description="Created",
        ordering="created_at",
    )
    def created_display(self, obj):

        return obj.created_at.strftime(
            "%d %b %Y"
        )

    @admin.display(
        description="Payment QR Summary",
    )
    def qr_summary(self, obj):

        if not obj or not obj.pk:

            return format_html(
                """
                <div style="
                    padding:12px;
                    background:#f8fafc;
                    border:1px solid #e5e7eb;
                    border-radius:8px;
                    color:#64748b;
                ">
                    {}
                </div>
                """,
                "Save the party first to add payment QR codes.",
            )

        qrs = obj.payment_qrs.all()
        count = qrs.count()

        if count == 0:

            return format_html(
                """
                <div style="
                    padding:12px;
                    background:#f8fafc;
                    border:1px solid #e5e7eb;
                    border-radius:8px;
                    color:#64748b;
                ">
                    {}
                </div>
                """,
                "No payment QR codes have been added yet.",
            )

        primary = qrs.filter(
            is_primary=True
        ).first()

        if primary:

            return format_html(
                """
                <div style="
                    padding:12px;
                    background:#ecfdf5;
                    border:1px solid #a7f3d0;
                    border-radius:8px;
                    color:#065f46;
                ">
                    <strong>{} payment QR code(s)</strong>

                    <div style="
                        margin-top:4px;
                        font-size:12px;
                    ">
                        Primary QR: {}
                    </div>
                </div>
                """,
                count,
                primary.qr_name,
            )

        return format_html(
            """
            <div style="
                padding:12px;
                background:#fffbeb;
                border:1px solid #fde68a;
                border-radius:8px;
                color:#92400e;
            ">
                <strong>{} payment QR code(s)</strong>

                <div style="
                    margin-top:4px;
                    font-size:12px;
                ">
                    No primary QR has been selected.
                </div>
            </div>
            """,
            count,
        )


# =========================================================
# PARTY PAYMENT QR ADMIN
# =========================================================

@admin.register(PartyPaymentQR)
class PartyPaymentQRAdmin(admin.ModelAdmin):

    form = PartyPaymentQRAdminForm

    list_display = (
        "qr_display",
        "party_display",
        "upi_display",
        "primary_display",
        "status_display",
        "created_display",
    )

    search_fields = (
        "id",
        "qr_name",
        "upi_id",
        "party__name",
        "party__contact_person",
        "party__phone",
        "party__email",
    )

    list_filter = (
        "is_primary",
        "is_active",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "party",
    )

    readonly_fields = (
        "id",
        "qr_preview",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-is_primary",
        "qr_name",
    )

    list_per_page = 25

    date_hierarchy = "created_at"

    actions = (
        activate_records,
        deactivate_records,
    )

    fieldsets = (
        (
            "Payment QR Information",
            {
                "fields": (
                    "id",
                    "party",
                    "qr_name",
                    "qr_image",
                    "qr_preview",
                    "upi_id",
                    "is_primary",
                    "is_active",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="QR")
    def qr_display(self, obj):

        if obj.qr_image:

            return format_html(
                """
                <img
                    src="{}"
                    alt="QR"
                    style="
                        width:60px;
                        height:60px;
                        object-fit:contain;
                        border:1px solid #e5e7eb;
                        border-radius:8px;
                        padding:4px;
                        background:#fff;
                    "
                >
                """,
                obj.qr_image.url,
            )

        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "No QR",
        )

    @admin.display(
        description="Party",
        ordering="party__name",
    )
    def party_display(self, obj):

        return format_html(
            "<strong>{}</strong>",
            obj.party.name,
        )

    @admin.display(
        description="UPI ID",
    )
    def upi_display(self, obj):

        if not obj.upi_id:

            return format_html(
                '<span style="color:#9ca3af;">{}</span>',
                "—",
            )

        return format_html(
            """
            <span style="
                font-family:monospace;
                font-size:11px;
            ">
                {}
            </span>
            """,
            obj.upi_id,
        )

    @admin.display(
        description="Primary",
    )
    def primary_display(self, obj):

        if obj.is_primary:

            return format_html(
                """
                <span style="
                    display:inline-block;
                    padding:4px 9px;
                    border-radius:999px;
                    background:#ecfdf5;
                    color:#047857;
                    font-size:11px;
                    font-weight:700;
                ">
                    {}
                </span>
                """,
                "Primary",
            )

        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "—",
        )

    @admin.display(
        description="Status",
        ordering="is_active",
    )
    def status_display(self, obj):

        if obj.is_active:

            return format_html(
                '<strong style="color:#166534;">{}</strong>',
                "Active",
            )

        return format_html(
            '<strong style="color:#991B1B;">{}</strong>',
            "Inactive",
        )

    @admin.display(
        description="Created",
        ordering="created_at",
    )
    def created_display(self, obj):

        return obj.created_at.strftime(
            "%d %b %Y"
        )

    @admin.display(description="QR Preview")
    def qr_preview(self, obj):

        if obj and obj.pk and obj.qr_image:

            return format_html(
                """
                <div style="
                    width:220px;
                    height:220px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    background:#ffffff;
                    border:1px solid #e5e7eb;
                    border-radius:12px;
                    padding:10px;
                ">
                    <img
                        src="{}"
                        alt="Payment QR"
                        style="
                            max-width:200px;
                            max-height:200px;
                            object-fit:contain;
                        "
                    >
                </div>
                """,
                obj.qr_image.url,
            )

        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "No QR image uploaded.",
        )

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if obj.is_primary:

            PartyPaymentQR.objects.filter(
                party=obj.party,
                is_primary=True,
            ).exclude(
                pk=obj.pk,
            ).update(
                is_primary=False,
            )

        super().save_model(
            request,
            obj,
            form,
            change,
        )


# =========================================================
# PAYMENT METHOD FORM
# =========================================================

class PaymentMethodAdminForm(forms.ModelForm):

    class Meta:
        model = PaymentMethod
        fields = "__all__"

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Example: UPI",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "placeholder": "Optional description",
                }
            ),
        }

    def clean_name(self):

        value = self.cleaned_data.get(
            "name",
            "",
        )

        value = " ".join(
            value.strip().split()
        )

        if not value:
            raise forms.ValidationError(
                "Payment method name is required."
            )

        return value


# =========================================================
# PAYMENT METHOD ADMIN
# =========================================================

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):

    form = PaymentMethodAdminForm

    list_display = (
        "name",
        "description",
        "payment_count",
        "status_badge",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "name",
        "description",
    )

    list_filter = (
        "is_active",
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "id",
        "payment_count",
        "created_at",
        "updated_at",
    )

    ordering = (
        "name",
    )

    list_per_page = 25

    date_hierarchy = "created_at"

    actions = (
        activate_records,
        deactivate_records,
    )

    fieldsets = (
        (
            "Payment Method",
            {
                "fields": (
                    "name",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "id",
                    "payment_count",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_queryset(self, request):

        return (
            super()
            .get_queryset(request)
            .annotate(
                _payment_count=Count(
                    "payments"
                )
            )
        )

    @admin.display(
        description="Payments",
        ordering="_payment_count",
    )
    def payment_count(self, obj):

        return obj._payment_count

    @admin.display(
        description="Status",
    )
    def status_badge(self, obj):

        if obj.is_active:

            return format_html(
                """
                <span style="
                    background:#DCFCE7;
                    color:#166534;
                    padding:4px 10px;
                    border-radius:999px;
                    font-weight:600;
                    font-size:12px;
                ">
                    {}
                </span>
                """,
                "Active",
            )

        return format_html(
            """
            <span style="
                background:#FEE2E2;
                color:#991B1B;
                padding:4px 10px;
                border-radius:999px;
                font-weight:600;
                font-size:12px;
            ">
                {}
            </span>
            """,
            "Inactive",
        )


# =========================================================
# PARTY ORDER FORM
# =========================================================

class PartyOrderAdminForm(forms.ModelForm):

    class Meta:
        model = PartyOrder
        fields = "__all__"

    def clean_gst_number(self):

        value = self.cleaned_data.get(
            "gst_number",
            "",
        ).strip().upper()

        if value and len(value) != 15:

            raise forms.ValidationError(
                "GST number must contain exactly 15 characters."
            )

        return value

    def clean(self):

        cleaned_data = super().clean()

        tax_type = cleaned_data.get(
            "tax_type"
        )

        gst_number = cleaned_data.get(
            "gst_number"
        )

        if (
            tax_type == PartyOrder.TaxType.GST
            and not gst_number
        ):

            self.add_error(
                "gst_number",
                "GST number is required when Tax Type is GST.",
            )

        # -----------------------------------------------------
        # AMOUNT VALIDATION
        # -----------------------------------------------------

        amount_fields = (
            "subtotal",
            "cgst_amount",
            "sgst_amount",
            "igst_amount",
            "other_charges",
            "discount_amount",
            "total_amount",
        )

        for field_name in amount_fields:

            value = cleaned_data.get(field_name)

            if value is not None and value < Decimal("0.00"):

                self.add_error(
                    field_name,
                    "Amount cannot be negative.",
                )

        return cleaned_data


# =========================================================
# PARTY ORDER ADMIN
# =========================================================

@admin.register(PartyOrder)
class PartyOrderAdmin(admin.ModelAdmin):

    form = PartyOrderAdminForm

    inlines = (
        PaymentInline,
    )

    list_display = (
        "order_number_display",
        "party_display",
        "order_date",
        "status_badge",
        "tax_type",
        "total_amount_display",
        "paid_amount_display",
        "outstanding_display",
        "payment_status_badge",
        "created_display",
    )

    search_fields = (
        "id",
        "order_number",
        "party__name",
        "party__contact_person",
        "party__phone",
        "party__email",
        "gst_number",
        "notes",
    )

    list_filter = (
        "status",
        "tax_type",
        "party",
        "is_active",
        "order_date",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "party",
    )

    readonly_fields = (
        "id",
        "order_number",
        "total_gst",
        "total_paid_display",
        "outstanding_amount_display",
        "payment_status_display",
        "created_at",
        "updated_at",
    )

    list_per_page = 25

    date_hierarchy = "order_date"

    ordering = (
        "-order_date",
        "-created_at",
    )

    actions = (
        activate_records,
        deactivate_records,
    )

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    "order_number",
                    "party",
                    "order_date",
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "GST Information",
            {
                "fields": (
                    "tax_type",
                    "gst_number",
                )
            },
        ),
        (
            "Amount Details",
            {
                "fields": (
                    "subtotal",
                    "cgst_amount",
                    "sgst_amount",
                    "igst_amount",
                    "total_gst",
                    "other_charges",
                    "discount_amount",
                    "total_amount",
                )
            },
        ),
        (
            "Payment Summary",
            {
                "fields": (
                    "total_paid_display",
                    "outstanding_amount_display",
                    "payment_status_display",
                )
            },
        ),
        (
            "Notes",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "notes",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_queryset(self, request):

        return (
            super()
            .get_queryset(request)
            .select_related(
                "party",
            )
            .annotate(
                _paid_amount=Sum(
                    "payments__amount",
                    filter=Q(
                        payments__status=(
                            Payment.PaymentStatus.COMPLETED
                        ),
                        payments__is_active=True,
                    ),
                )
            )
        )

    @admin.display(
        description="Order",
        ordering="order_number",
    )
    def order_number_display(self, obj):

        return format_html(
            """
            <strong style="
                color:#153030;
                font-family:monospace;
                font-size:12px;
            ">
                {}
            </strong>
            """,
            obj.order_number,
        )

    @admin.display(
        description="Party",
        ordering="party__name",
    )
    def party_display(self, obj):

        return obj.party.name

    @admin.display(
        description="Total",
        ordering="total_amount",
    )
    def total_amount_display(self, obj):

        return currency_html(
            obj.total_amount,
            color="#153030",
            strong=True,
        )

    @admin.display(
        description="Paid",
        ordering="_paid_amount",
    )
    def paid_amount_display(self, obj):

        amount = (
            obj._paid_amount
            or Decimal("0.00")
        )

        return currency_html(
            amount,
            color="#166534",
            strong=True,
        )

    @admin.display(
        description="Outstanding",
    )
    def outstanding_display(self, obj):

        paid = (
            obj._paid_amount
            or Decimal("0.00")
        )

        amount = (
            obj.total_amount - paid
        )

        if amount < Decimal("0.00"):
            amount = Decimal("0.00")

        if amount == Decimal("0.00"):

            return currency_html(
                amount,
                color="#166534",
                strong=True,
            )

        return currency_html(
            amount,
            color="#b91c1c",
            strong=True,
        )

    @admin.display(
        description="Order Status",
        ordering="status",
    )
    def status_badge(self, obj):

        styles = {
            "PENDING": (
                "#FEF3C7",
                "#92400E",
                "Pending",
            ),
            "CONFIRMED": (
                "#DBEAFE",
                "#1E40AF",
                "Confirmed",
            ),
            "COMPLETED": (
                "#DCFCE7",
                "#166534",
                "Completed",
            ),
            "CANCELLED": (
                "#FEE2E2",
                "#991B1B",
                "Cancelled",
            ),
        }

        bg, text, label = styles.get(
            obj.status,
            (
                "#F3F4F6",
                "#374151",
                obj.status,
            ),
        )

        return format_html(
            """
            <span style="
                background:{};
                color:{};
                padding:4px 10px;
                border-radius:999px;
                font-weight:600;
                font-size:12px;
            ">
                {}
            </span>
            """,
            bg,
            text,
            label,
        )

    @admin.display(
        description="Payment Status",
    )
    def payment_status_badge(self, obj):

        paid = (
            obj._paid_amount
            or Decimal("0.00")
        )

        total = (
            obj.total_amount
            or Decimal("0.00")
        )

        if total <= Decimal("0.00"):

            label = "No Amount"
            bg = "#F3F4F6"
            text = "#6B7280"

        elif paid <= Decimal("0.00"):

            label = "Unpaid"
            bg = "#FEE2E2"
            text = "#991B1B"

        elif paid >= total:

            label = "Paid"
            bg = "#DCFCE7"
            text = "#166534"

        else:

            label = "Partially Paid"
            bg = "#FEF3C7"
            text = "#92400E"

        return format_html(
            """
            <span style="
                background:{};
                color:{};
                padding:4px 10px;
                border-radius:999px;
                font-weight:600;
                font-size:12px;
            ">
                {}
            </span>
            """,
            bg,
            text,
            label,
        )

    @admin.display(
        description="Total GST",
    )
    def total_gst(self, obj):

        return currency_html(
            obj.total_gst,
            strong=False,
        )

    @admin.display(
        description="Total Paid",
    )
    def total_paid_display(self, obj):

        return currency_html(
            obj.total_paid,
            color="#166534",
            strong=True,
        )

    @admin.display(
        description="Outstanding",
    )
    def outstanding_amount_display(self, obj):

        amount = obj.outstanding_amount

        if amount < Decimal("0.00"):
            amount = Decimal("0.00")

        color = (
            "#166534"
            if amount == Decimal("0.00")
            else "#b91c1c"
        )

        return currency_html(
            amount,
            color=color,
            strong=True,
        )

    @admin.display(
        description="Payment Status",
    )
    def payment_status_display(self, obj):

        labels = {
            "NO_AMOUNT": "No Amount",
            "UNPAID": "Unpaid",
            "PARTIALLY_PAID": "Partially Paid",
            "PAID": "Paid",
        }

        status = obj.payment_status

        return labels.get(
            status,
            status,
        )

    @admin.display(
        description="Created",
        ordering="created_at",
    )
    def created_display(self, obj):

        return obj.created_at.strftime(
            "%d %b %Y"
        )


# =========================================================
# PAYMENT FORM
# =========================================================

class PaymentAdminForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = "__all__"

        widgets = {
            "transaction_reference": forms.TextInput(
                attrs={
                    "placeholder": "UPI / bank transaction reference",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "placeholder": "Optional payment notes",
                    "rows": 3,
                }
            ),
        }

    def clean_amount(self):

        amount = self.cleaned_data.get(
            "amount"
        )

        if amount is None:
            return amount

        if amount <= Decimal("0.00"):

            raise forms.ValidationError(
                "Payment amount must be greater than zero."
            )

        return amount

    def clean_transaction_reference(self):

        return self.cleaned_data.get(
            "transaction_reference",
            "",
        ).strip()

    def clean_notes(self):

        return self.cleaned_data.get(
            "notes",
            "",
        ).strip()


# =========================================================
# PAYMENT ADMIN
# =========================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    form = PaymentAdminForm

    list_display = (
        "payment_number_display",
        "order_display",
        "party_display",
        "payment_date",
        "payment_method",
        "amount_display",
        "status_badge",
        "transaction_reference_display",
        "created_display",
    )

    search_fields = (
        "id",
        "payment_number",
        "order__order_number",
        "order__party__name",
        "order__party__contact_person",
        "order__party__phone",
        "order__party__email",
        "transaction_reference",
        "notes",
    )

    list_filter = (
        "status",
        "payment_method",
        "payment_date",
        "is_active",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "order",
        "payment_method",
    )

    readonly_fields = (
        "id",
        "payment_number",
        "order_total_display",
        "order_paid_display",
        "order_outstanding_display",
        "created_at",
        "updated_at",
    )

    list_per_page = 25

    date_hierarchy = "payment_date"

    ordering = (
        "-payment_date",
        "-created_at",
    )

    actions = (
        activate_records,
        deactivate_records,
    )

    fieldsets = (
        (
            "Payment Information",
            {
                "fields": (
                    "payment_number",
                    "order",
                    "payment_date",
                    "payment_method",
                    "amount",
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Order Payment Summary",
            {
                "fields": (
                    "order_total_display",
                    "order_paid_display",
                    "order_outstanding_display",
                )
            },
        ),
        (
            "Transaction Details",
            {
                "fields": (
                    "transaction_reference",
                    "notes",
                )
            },
        ),
        (
            "System Information",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_queryset(self, request):

        return (
            super()
            .get_queryset(request)
            .select_related(
                "order",
                "order__party",
                "payment_method",
            )
        )

    @admin.display(
        description="Payment",
        ordering="payment_number",
    )
    def payment_number_display(self, obj):

        return format_html(
            """
            <strong style="
                color:#153030;
                font-family:monospace;
                font-size:12px;
            ">
                {}
            </strong>
            """,
            obj.payment_number,
        )

    @admin.display(
        description="Order",
        ordering="order__order_number",
    )
    def order_display(self, obj):

        return format_html(
            """
            <strong style="
                font-family:monospace;
                font-size:11px;
            ">
                {}
            </strong>
            """,
            obj.order.order_number,
        )

    @admin.display(
        description="Party",
        ordering="order__party__name",
    )
    def party_display(self, obj):

        return obj.order.party.name

    @admin.display(
        description="Amount",
        ordering="amount",
    )
    def amount_display(self, obj):

        return currency_html(
            obj.amount,
            strong=True,
        )

    @admin.display(
        description="Status",
        ordering="status",
    )
    def status_badge(self, obj):

        styles = {
            "PENDING": (
                "#FEF3C7",
                "#92400E",
                "Pending",
            ),
            "COMPLETED": (
                "#DCFCE7",
                "#166534",
                "Completed",
            ),
            "FAILED": (
                "#FEE2E2",
                "#991B1B",
                "Failed",
            ),
            "CANCELLED": (
                "#FEE2E2",
                "#991B1B",
                "Cancelled",
            ),
        }

        bg, text, label = styles.get(
            obj.status,
            (
                "#F3F4F6",
                "#374151",
                obj.status,
            ),
        )

        return format_html(
            """
            <span style="
                background:{};
                color:{};
                padding:4px 10px;
                border-radius:999px;
                font-weight:600;
                font-size:12px;
            ">
                {}
            </span>
            """,
            bg,
            text,
            label,
        )

    @admin.display(
        description="Reference",
    )
    def transaction_reference_display(self, obj):

        if obj.transaction_reference:

            return obj.transaction_reference

        return format_html(
            '<span style="color:#9CA3AF;">{}</span>',
            "—",
        )

    @admin.display(
        description="Order Total",
    )
    def order_total_display(self, obj):

        return currency_html(
            obj.order.total_amount,
            strong=True,
        )

    @admin.display(
        description="Total Paid",
    )
    def order_paid_display(self, obj):

        return currency_html(
            obj.order.total_paid,
            color="#166534",
            strong=True,
        )

    @admin.display(
        description="Outstanding",
    )
    def order_outstanding_display(self, obj):

        amount = obj.order.outstanding_amount

        if amount < Decimal("0.00"):
            amount = Decimal("0.00")

        color = (
            "#166534"
            if amount == Decimal("0.00")
            else "#b91c1c"
        )

        return currency_html(
            amount,
            color=color,
            strong=True,
        )

    @admin.display(
        description="Created",
        ordering="created_at",
    )
    def created_display(self, obj):

        return obj.created_at.strftime(
            "%d %b %Y"
        )