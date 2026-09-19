from decimal import Decimal
from django.contrib import admin, messages
from django.utils.html import format_html
from .models import (
    Party,
    PartyPaymentQR,
    PaymentMethod,
    PartyPurchase,
    PurchasePaymentInstallment,
)
from pathlib import Path as FilePath
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.utils.safestring import mark_safe

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def money(value):
    """
    Format Decimal values BEFORE passing them to format_html().

    Django 6.1 converts format_html arguments to SafeString,
    therefore {:,.2f} must NOT be used directly inside format_html().
    """
    if value is None:
        value = Decimal("0.00")

    return f"{Decimal(value):,.2f}"


# =========================================================
# PARTY PAYMENT QR INLINE
# =========================================================

class PartyPaymentQRInline(admin.TabularInline):

    model = PartyPaymentQR

    extra = 0

    show_change_link = True

    fields = (
        "qr_name",
        "qr_image",
        "upi_id",
        "is_primary",
    )

    ordering = (
        "-is_primary",
        "qr_name",
    )


# =========================================================
# PURCHASE PAYMENT INSTALLMENT INLINE
# =========================================================

class PurchasePaymentInstallmentInline(admin.TabularInline):

    model = PurchasePaymentInstallment

    extra = 0

    show_change_link = True

    ordering = (
        "installment_number",
    )

    autocomplete_fields = (
        "payment_method",
    )

    fields = (
        "installment_number",
        "due_date",
        "installment_amount",
        "paid_amount",
        "remaining_amount",
        "payment_method",
        "payment_date",
        "transaction_reference",
        "status",
        "notes",
    )

    readonly_fields = (
        "remaining_amount",
        "status",
    )


# =========================================================
# PARTY ADMIN
# =========================================================

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):

    list_display = (
        "party_name",
        "party_type_badge",
        "contact_person",
        "phone",
        "email",
        "city",
        "state",
        "gst_number",
        "purchase_count",
    )

    search_fields = (
        "name",
        "contact_person",
        "phone",
        "alternate_phone",
        "email",
        "gst_number",
        "city",
        "state",
        "pincode",
        "gpay_number",
        "bank_name",
        "account_holder_name",
        "account_number",
        "ifsc_code",
        "branch_name",
        "upi_id",
    )

    list_filter = (
        "party_type",
        "state",
        "city",
    )

    ordering = (
        "name",
    )

    list_per_page = 25

    date_hierarchy = "created_at"

    readonly_fields = (
        "party_summary",
        "purchase_count",
        "created_at",
        "updated_at",
    )

    inlines = (
        PartyPaymentQRInline,
    )

    fieldsets = (

        (
            "Party Information",
            {
                "fields": (
                    "name",
                    "party_type",
                    "contact_person",
                ),
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
                ),
            },
        ),

        (
            "Address Information",
            {
                "fields": (
                    "address",
                    "city",
                    "state",
                    "pincode",
                ),
            },
        ),

        (
            "GST Information",
            {
                "fields": (
                    "gst_number",
                ),
            },
        ),

        (
            "Bank Information",
            {
                "fields": (
                    "bank_name",
                    "account_holder_name",
                    "account_number",
                    "ifsc_code",
                    "branch_name",
                    "upi_id",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),

        (
            "Party Summary",
            {
                "fields": (
                    "party_summary",
                    "purchase_count",
                ),
            },
        ),

        (
            "Notes",
            {
                "fields": (
                    "notes",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(
        description="Party",
        ordering="name",
    )
    def party_name(self, obj):

        if not obj:
            return "-"

        return format_html(
            "<strong>{}</strong>",
            obj.name,
        )

    @admin.display(
        description="Type",
        ordering="party_type",
    )
    def party_type_badge(self, obj):

        colors = {
            "MANUFACTURER": "#2563eb",
            "WHOLESALER": "#7c3aed",
            "DISTRIBUTOR": "#0891b2",
            "OTHER": "#6b7280",
        }

        color = colors.get(
            obj.party_type,
            "#6b7280",
        )

        return format_html(
            "<span style='"
            "background:{};"
            "color:white;"
            "padding:5px 9px;"
            "border-radius:14px;"
            "font-size:11px;"
            "font-weight:600;"
            "'>{}</span>",
            color,
            obj.get_party_type_display(),
        )

    @admin.display(
        description="Purchases",
    )
    def purchase_count(self, obj):

        if not obj:
            return 0

        return obj.purchases.count()

    @admin.display(
        description="Party Summary",
    )
    def party_summary(self, obj):

        if not obj:
            return "-"

        return format_html(
            """
            <div style="
                background:#f8fafc;
                border:1px solid #e2e8f0;
                border-radius:10px;
                padding:18px;
                max-width:650px;
                line-height:1.8;
            ">

                <h3>Party Summary</h3>

                <p>
                    <strong>Name:</strong> {}
                </p>

                <p>
                    <strong>Type:</strong> {}
                </p>

                <p>
                    <strong>Contact Person:</strong> {}
                </p>

                <p>
                    <strong>Phone:</strong> {}
                </p>

                <p>
                    <strong>Email:</strong> {}
                </p>

                <p>
                    <strong>GST:</strong> {}
                </p>

                <p>
                    <strong>Location:</strong>
                    {}, {}, {}
                </p>

                <p>
                    <strong>UPI:</strong> {}
                </p>

            </div>
            """,
            obj.name,
            obj.get_party_type_display(),
            obj.contact_person or "-",
            obj.phone or "-",
            obj.email or "-",
            obj.gst_number or "-",
            obj.city or "-",
            obj.state or "-",
            obj.pincode or "-",
            obj.upi_id or "-",
        )


# =========================================================
# PARTY PAYMENT QR ADMIN
# =========================================================

@admin.register(PartyPaymentQR)
class PartyPaymentQRAdmin(admin.ModelAdmin):

    list_display = (
        "qr_name_display",
        "party_name",
        "upi_id_display",
        "primary_badge",
        "qr_image_preview",
    )

    search_fields = (
        "qr_name",
        "upi_id",
        "party__name",
        "party__phone",
        "party__email",
    )

    list_filter = (
        "is_primary",
        "party",
    )

    ordering = (
        "-is_primary",
        "qr_name",
    )

    list_per_page = 25

    autocomplete_fields = (
        "party",
    )

    readonly_fields = (
        "qr_image_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "QR Information",
            {
                "fields": (
                    "party",
                    "qr_name",
                    "upi_id",
                    "is_primary",
                ),
            },
        ),

        (
            "QR Image",
            {
                "fields": (
                    "qr_image",
                    "qr_image_preview",
                ),
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(
        description="QR Name",
        ordering="qr_name",
    )
    def qr_name_display(self, obj):

        if not obj:
            return "-"

        return format_html(
            "<strong>{}</strong>",
            obj.qr_name,
        )

    @admin.display(
        description="Party",
        ordering="party__name",
    )
    def party_name(self, obj):

        if not obj or not obj.party:
            return "-"

        return obj.party.name

    @admin.display(
        description="UPI ID",
        ordering="upi_id",
    )
    def upi_id_display(self, obj):

        if not obj:
            return "-"

        return obj.upi_id or "-"

    @admin.display(
        description="Primary",
        boolean=True,
    )
    def primary_badge(self, obj):

        if not obj:
            return False

        return obj.is_primary

    @admin.display(
        description="QR Preview",
    )
    def qr_image_preview(self, obj):

        if obj and obj.qr_image:

            return format_html(
                "<img src='{}' "
                "style='"
                "width:120px;"
                "height:120px;"
                "object-fit:contain;"
                "border:1px solid #e5e7eb;"
                "border-radius:8px;"
                "padding:5px;"
                "background:white;"
                "' />",
                obj.qr_image.url,
            )

        return format_html(
            "<span style='color:#9ca3af;'>{}</span>",
            "No QR Image",
        )


# =========================================================
# PAYMENT METHOD ADMIN
# =========================================================

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):

    list_display = (
        "name_display",
        "description",
        "purchase_installment_count",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "name",
    )

    list_per_page = 25

    readonly_fields = (
        "purchase_installment_count",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Payment Method",
            {
                "fields": (
                    "name",
                    "description",
                ),
            },
        ),

        (
            "Usage",
            {
                "fields": (
                    "purchase_installment_count",
                ),
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(
        description="Payment Method",
        ordering="name",
    )
    def name_display(self, obj):

        if not obj:
            return "-"

        return format_html(
            "<strong>{}</strong>",
            obj.name,
        )

    @admin.display(
        description="Installments",
    )
    def purchase_installment_count(self, obj):

        if not obj:
            return 0

        return obj.purchase_installments.count()


# =========================================================
# PARTY PURCHASE ADMIN
# =========================================================




# ============================================================
# PARTY PURCHASE ADMIN FORM
# ============================================================

class PartyPurchaseAdminForm(forms.ModelForm):
    """
    Admin form for PartyPurchase.

    The model already contains:
    - GST / Non-GST bill type
    - supplier invoice number/date
    - supplier invoice document
    - CGST / SGST / IGST
    - automatic purchase calculations
    - automatic paid / due / payment status
    """

    class Meta:
        model = PartyPurchase
        fields = "__all__"
        widgets = {
            "purchase_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "invoice_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "invoice_document": forms.ClearableFileInput(
                attrs={
                    "accept": ".pdf,.jpg,.jpeg,.png,.webp",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Add supplier bill notes, transport details, "
                        "payment notes or any other purchase information."
                    ),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        bill_type = cleaned_data.get("bill_type")

        cgst = cleaned_data.get("cgst_percent") or Decimal("0.00")
        sgst = cleaned_data.get("sgst_percent") or Decimal("0.00")
        igst = cleaned_data.get("igst_percent") or Decimal("0.00")

        purchase_date = cleaned_data.get("purchase_date")
        invoice_date = cleaned_data.get("invoice_date")

        # ----------------------------------------------------
        # GST / NON-GST VALIDATION
        # ----------------------------------------------------

        if bill_type == PartyPurchase.BillType.NON_GST:
            if cgst > 0 or sgst > 0 or igst > 0:
                raise ValidationError(
                    "Non-GST Bill cannot contain CGST, SGST or IGST. "
                    "Set all GST percentages to 0%."
                )

        if bill_type == PartyPurchase.BillType.GST:
            if igst > 0 and (cgst > 0 or sgst > 0):
                raise ValidationError(
                    "Use either IGST or CGST + SGST. "
                    "Do not use IGST together with CGST/SGST."
                )

        # ----------------------------------------------------
        # INVOICE DATE VALIDATION
        # ----------------------------------------------------

        if purchase_date and invoice_date:
            if invoice_date > purchase_date:
                raise ValidationError(
                    "Supplier invoice date cannot be later than purchase date."
                )

        # ----------------------------------------------------
        # DOCUMENT VALIDATION
        # ----------------------------------------------------

        document = cleaned_data.get("invoice_document")

        if document:
            extension = FilePath(document.name).suffix.lower()

            allowed_extensions = {
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            }

            if extension not in allowed_extensions:
                raise ValidationError(
                    "Invalid document type. Allowed: PDF, JPG, JPEG, PNG, WEBP."
                )

            max_size = 10 * 1024 * 1024
            if getattr(document, "size", 0) > max_size:
                raise ValidationError(
                    "Bill document must be 10 MB or smaller."
                )

        return cleaned_data


# ============================================================
# PARTY PURCHASE ADMIN
# ============================================================

@admin.register(PartyPurchase)
class PartyPurchaseAdmin(admin.ModelAdmin):

    form = PartyPurchaseAdminForm

    # --------------------------------------------------------
    # LIST PAGE
    # --------------------------------------------------------

    list_display = (
        "purchase_number_display",
        "party_display",
        "purchase_date",
        "bill_type_badge",
        "invoice_number_display",
        "status_badge",
        "payment_status_badge",
        "grand_total_display",
        "paid_amount_display",
        "due_amount_display",
        "document_type_display",
    )

    list_display_links = (
        "purchase_number_display",
        "party_display",
    )

    search_fields = (
        "purchase_number",
        "invoice_number",
        "party__name",
    )

    list_filter = (
        "bill_type",
        "status",
        "payment_status",
        "purchase_date",
        "invoice_date",
    )

    date_hierarchy = "purchase_date"

    ordering = (
        "-purchase_date",
        "-created_at",
    )

    list_per_page = 30

    list_select_related = (
        "party",
    )

    autocomplete_fields = (
        "party",
    )

    preserve_filters = True
    save_on_top = True
    empty_value_display = "—"

    # --------------------------------------------------------
    # READONLY / CALCULATED FIELDS
    # --------------------------------------------------------

    readonly_fields = (
        "purchase_number",
        "payment_status",
        "discount_amount",
        "taxable_amount",
        "cgst_amount",
        "sgst_amount",
        "igst_amount",
        "round_off",
        "grand_total",
        "paid_amount",
        "due_amount",
        "document_type_display",
        "bill_document_preview",
        "gst_summary",
        "payment_summary",
        "created_at",
        "updated_at",
    )

    # --------------------------------------------------------
    # FORM LAYOUT
    # --------------------------------------------------------

    fieldsets = (
        (
            "Purchase Information",
            {
                "classes": ("wide",),
                "fields": (
                    "purchase_number",
                    "party",
                    "purchase_date",
                    "status",
                ),
                "description": (
                    "Purchase number is generated automatically. "
                    "Select the supplier and purchase status."
                ),
            },
        ),

        (
            "Supplier Bill / Invoice",
            {
                "classes": ("wide",),
                "fields": (
                    "bill_type",
                    "invoice_number",
                    "invoice_date",
                    "invoice_document",
                    "document_type_display",
                    "bill_document_preview",
                ),
                "description": (
                    "Choose GST Bill or Non-GST Bill. "
                    "Upload the supplier invoice in PDF, JPG, JPEG, PNG or WEBP format."
                ),
            },
        ),

        (
            "Purchase Amount",
            {
                "classes": ("wide",),
                "fields": (
                    "subtotal",
                    "discount_percent",
                    "discount_amount",
                    "taxable_amount",
                    "other_charges",
                ),
            },
        ),

        (
            "GST / Tax Details",
            {
                "classes": ("wide",),
                "fields": (
                    "gst_summary",
                    "cgst_percent",
                    "cgst_amount",
                    "sgst_percent",
                    "sgst_amount",
                    "igst_percent",
                    "igst_amount",
                ),
                "description": (
                    "GST Bill: use either CGST + SGST or IGST. "
                    "Non-GST Bill: CGST, SGST and IGST must be 0%."
                ),
            },
        ),

        (
            "Calculated Total",
            {
                "classes": ("wide",),
                "fields": (
                    "round_off",
                    "grand_total",
                ),
                "description": (
                    "Discount amount, taxable amount, GST amounts, "
                    "round-off and grand total are calculated automatically."
                ),
            },
        ),

        (
            "Payment Summary",
            {
                "classes": ("wide",),
                "fields": (
                    "payment_summary",
                    "paid_amount",
                    "due_amount",
                    "payment_status",
                ),
                "description": (
                    "Paid amount and due amount are automatically calculated "
                    "from the purchase payment records used by your model."
                ),
            },
        ),

        (
            "Notes",
            {
                "classes": ("wide",),
                "fields": (
                    "notes",
                ),
            },
        ),

        (
            "System Information",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    # --------------------------------------------------------
    # PURCHASE NUMBER
    # --------------------------------------------------------

    @admin.display(
        description="Purchase No.",
        ordering="purchase_number",
    )
    def purchase_number_display(self, obj):
        return format_html(
            '<strong style="color:#153030;">{}</strong>',
            obj.purchase_number or "—",
        )

    # --------------------------------------------------------
    # PARTY
    # --------------------------------------------------------

    @admin.display(
        description="Supplier",
        ordering="party__name",
    )
    def party_display(self, obj):
        if not obj.party:
            return "—"

        name = getattr(obj.party, "name", None)

        return format_html(
            '<strong>{}</strong>',
            name or str(obj.party),
        )

    # --------------------------------------------------------
    # BILL TYPE
    # --------------------------------------------------------

    @admin.display(
        description="Bill Type",
        ordering="bill_type",
    )
    def bill_type_badge(self, obj):

        if obj.bill_type == PartyPurchase.BillType.GST:
            return mark_safe(
                '<span style="display:inline-block;'
                'padding:5px 10px;border-radius:999px;'
                'background:#dcfce7;color:#166534;'
                'font-size:11px;font-weight:800;">'
                'GST BILL'
                '</span>'
            )

        return mark_safe(
            '<span style="display:inline-block;'
            'padding:5px 10px;border-radius:999px;'
            'background:#f3f4f6;color:#374151;'
            'font-size:11px;font-weight:800;">'
            'NON-GST BILL'
            '</span>'
        )

    # --------------------------------------------------------
    # INVOICE
    # --------------------------------------------------------

    @admin.display(
        description="Invoice No.",
        ordering="invoice_number",
    )
    def invoice_number_display(self, obj):
        return obj.invoice_number or "—"

    # --------------------------------------------------------
    # PURCHASE STATUS
    # --------------------------------------------------------

    @admin.display(
        description="Status",
        ordering="status",
    )
    def status_badge(self, obj):

        colors = {
            "DRAFT": ("#f3f4f6", "#374151"),
            "CONFIRMED": ("#dbeafe", "#1d4ed8"),
            "RECEIVED": ("#dcfce7", "#166534"),
            "PARTIAL": ("#fef3c7", "#92400e"),
            "CANCELLED": ("#fee2e2", "#991b1b"),
        }

        bg, fg = colors.get(
            obj.status,
            ("#f3f4f6", "#374151"),
        )

        return format_html(
            '<span style="display:inline-block;'
            'padding:5px 9px;border-radius:999px;'
            'background:{};color:{};'
            'font-size:11px;font-weight:800;">'
            '{}</span>',
            bg,
            fg,
            obj.get_status_display(),
        )

    # --------------------------------------------------------
    # PAYMENT STATUS
    # --------------------------------------------------------

    @admin.display(
        description="Payment",
        ordering="payment_status",
    )
    def payment_status_badge(self, obj):

        colors = {
            "UNPAID": ("#fee2e2", "#991b1b"),
            "PARTIAL": ("#fef3c7", "#92400e"),
            "PAID": ("#dcfce7", "#166534"),
        }

        bg, fg = colors.get(
            obj.payment_status,
            ("#f3f4f6", "#374151"),
        )

        return format_html(
            '<span style="display:inline-block;'
            'padding:5px 9px;border-radius:999px;'
            'background:{};color:{};'
            'font-size:11px;font-weight:800;">'
            '{}</span>',
            bg,
            fg,
            obj.get_payment_status_display(),
        )

    # --------------------------------------------------------
    # MONEY
    # --------------------------------------------------------

    @admin.display(
        description="Grand Total",
        ordering="grand_total",
    )
    def grand_total_display(self, obj):
        return format_html(
            "<strong>₹ {}</strong>",
            money(obj.grand_total),
        )

    @admin.display(
        description="Paid",
        ordering="paid_amount",
    )
    def paid_amount_display(self, obj):
        return format_html(
            '<span style="color:#166534;font-weight:800;">'
            '₹ {}'
            '</span>',
            money(obj.paid_amount),
        )

    @admin.display(
        description="Due",
        ordering="due_amount",
    )
    def due_amount_display(self, obj):

        due = obj.due_amount or Decimal("0.00")

        if due > 0:
            return format_html(
                '<span style="color:#b45309;font-weight:800;">'
                '₹ {}'
                '</span>',
                money(due),
            )

        return mark_safe(
            '<span style="color:#166534;font-weight:800;">'
            '₹ 0.00'
            '</span>'
        )

    # --------------------------------------------------------
    # DOCUMENT TYPE
    # --------------------------------------------------------

    @admin.display(
        description="Document Type",
    )
    def document_type_display(self, obj):

        if not obj or not obj.invoice_document:
            return mark_safe(
                '<span style="color:#9ca3af;font-weight:600;">'
                'No document'
                '</span>'
            )

        extension = (
            FilePath(obj.invoice_document.name)
            .suffix
            .lower()
            .replace(".", "")
        )

        labels = {
            "pdf": "PDF",
            "jpg": "JPG IMAGE",
            "jpeg": "JPEG IMAGE",
            "png": "PNG IMAGE",
            "webp": "WEBP IMAGE",
        }

        label = labels.get(
            extension,
            extension.upper() if extension else "FILE",
        )

        return format_html(
            '<span style="display:inline-block;'
            'padding:5px 9px;border-radius:7px;'
            'background:#eef2ff;color:#3730a3;'
            'font-size:11px;font-weight:800;">'
            '{}'
            '</span>',
            label,
        )

    # --------------------------------------------------------
    # DOCUMENT PREVIEW
    # --------------------------------------------------------

    @admin.display(description="Uploaded Bill")
    def bill_document_preview(self, obj):

        if not obj or not obj.invoice_document:
            return mark_safe(
                '<div style="padding:12px;border:1px dashed #d1d5db;'
                'border-radius:9px;color:#6b7280;">'
                'No supplier bill document uploaded.'
                '</div>'
            )

        url = obj.invoice_document.url
        name = FilePath(obj.invoice_document.name).name
        extension = FilePath(name).suffix.lower()

        if extension in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }:
            return format_html(
                '<div style="display:flex;align-items:center;'
                'gap:14px;padding:12px;border:1px solid #e5e7eb;'
                'border-radius:10px;background:#fafafa;">'
                '<img src="{}" alt="Supplier bill" '
                'style="width:110px;height:110px;object-fit:cover;'
                'border-radius:8px;border:1px solid #e5e7eb;">'
                '<div>'
                '<strong>{}</strong><br>'
                '<small style="color:#6b7280;">{}</small><br><br>'
                '<a href="{}" target="_blank" rel="noopener noreferrer" '
                'style="display:inline-block;padding:7px 12px;'
                'border-radius:7px;background:#153030;color:white;'
                'text-decoration:none;font-weight:700;">'
                'Open Document'
                '</a>'
                '</div>'
                '</div>',
                url,
                name,
                extension.replace(".", "").upper(),
                url,
            )

        return format_html(
            '<div style="padding:14px;border:1px solid #e5e7eb;'
            'border-radius:10px;background:#fafafa;">'
            '<strong>{}</strong><br>'
            '<small style="color:#6b7280;">{}</small><br><br>'
            '<a href="{}" target="_blank" rel="noopener noreferrer" '
            'style="display:inline-block;padding:7px 12px;'
            'border-radius:7px;background:#153030;color:white;'
            'text-decoration:none;font-weight:700;">'
            'Open / View Document'
            '</a>'
            '</div>',
            name,
            extension.replace(".", "").upper() or "FILE",
            url,
        )

    # --------------------------------------------------------
    # GST SUMMARY
    # --------------------------------------------------------

    @admin.display(description="GST Calculation")
    def gst_summary(self, obj):

        if obj.bill_type == PartyPurchase.BillType.NON_GST:
            return mark_safe(
                '<div style="padding:12px;border-radius:9px;'
                'background:#f9fafb;border:1px solid #e5e7eb;">'
                '<strong>NON-GST BILL</strong><br>'
                '<small style="color:#6b7280;">'
                'GST calculation is disabled for this bill.'
                '</small>'
                '</div>'
            )

        cgst_percent = money(obj.cgst_percent).replace(".00", "")
        sgst_percent = money(obj.sgst_percent).replace(".00", "")
        igst_percent = money(obj.igst_percent).replace(".00", "")

        return format_html(
            '<div style="display:flex;gap:8px;flex-wrap:wrap;">'
            '<div style="padding:10px 12px;border:1px solid #e5e7eb;'
            'border-radius:8px;min-width:130px;">'
            '<small>CGST</small><br>'
            '<strong>{}%</strong> · ₹ {}'
            '</div>'
            '<div style="padding:10px 12px;border:1px solid #e5e7eb;'
            'border-radius:8px;min-width:130px;">'
            '<small>SGST</small><br>'
            '<strong>{}%</strong> · ₹ {}'
            '</div>'
            '<div style="padding:10px 12px;border:1px solid #e5e7eb;'
            'border-radius:8px;min-width:130px;">'
            '<small>IGST</small><br>'
            '<strong>{}%</strong> · ₹ {}'
            '</div>'
            '</div>',
            cgst_percent,
            money(obj.cgst_amount),
            sgst_percent,
            money(obj.sgst_amount),
            igst_percent,
            money(obj.igst_amount),
        )

    # --------------------------------------------------------
    # PAYMENT SUMMARY
    # --------------------------------------------------------

    @admin.display(description="Payment Summary")
    def payment_summary(self, obj):

        total = obj.grand_total or Decimal("0.00")
        paid = obj.paid_amount or Decimal("0.00")
        due = obj.due_amount or Decimal("0.00")

        percentage = Decimal("0.00")

        if total > 0:
            percentage = (
                paid * Decimal("100")
            ) / total

        if percentage > 100:
            percentage = Decimal("100")

        return format_html(
            '<div style="min-width:360px;max-width:650px;">'
            '<div style="display:flex;justify-content:space-between;'
            'gap:15px;margin-bottom:8px;">'
            '<span><strong>Paid:</strong> ₹ {}</span>'
            '<span><strong>Due:</strong> ₹ {}</span>'
            '</div>'
            '<div style="height:9px;background:#e5e7eb;'
            'border-radius:999px;overflow:hidden;">'
            '<div style="height:100%;width:{}%;'
            'background:#153030;border-radius:999px;"></div>'
            '</div>'
            '<small style="display:block;margin-top:6px;color:#6b7280;">'
            '{}% paid'
            '</small>'
            '</div>',
            money(paid),
            money(due),
            percentage,
            percentage.quantize(Decimal("0.1")),
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    def save_model(self, request, obj, form, change):
        """
        The model's save() performs the financial calculations.
        Admin simply saves the object inside a transaction.
        """
        try:
            with transaction.atomic():
                super().save_model(
                    request,
                    obj,
                    form,
                    change,
                )

        except ValidationError:
            raise

        self.message_user(
            request,
            (
                "Purchase saved successfully. "
                "GST, totals and payment summary were recalculated."
            ),
            messages.SUCCESS,
        )

    # --------------------------------------------------------
    # ADMIN ACTIONS
    # --------------------------------------------------------

    @admin.action(description="Mark selected purchases as Confirmed")
    def mark_confirmed(self, request, queryset):

        updated = queryset.exclude(
            status=PartyPurchase.Status.CANCELLED
        ).update(
            status=PartyPurchase.Status.CONFIRMED
        )

        self.message_user(
            request,
            f"{updated} purchase(s) marked as Confirmed.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark selected purchases as Received")
    def mark_received(self, request, queryset):

        updated = queryset.exclude(
            status=PartyPurchase.Status.CANCELLED
        ).update(
            status=PartyPurchase.Status.RECEIVED
        )

        self.message_user(
            request,
            f"{updated} purchase(s) marked as Received.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark selected purchases as Cancelled")
    def mark_cancelled(self, request, queryset):

        updated = queryset.update(
            status=PartyPurchase.Status.CANCELLED
        )

        self.message_user(
            request,
            f"{updated} purchase(s) marked as Cancelled.",
            messages.WARNING,
        )

    @admin.action(description="Recalculate selected purchases")
    def recalculate_amounts(self, request, queryset):

        success = 0
        failed = 0

        for purchase in queryset:
            try:
                purchase.calculate_amounts()
                purchase.save()
                success += 1
            except ValidationError:
                failed += 1

        if success:
            self.message_user(
                request,
                f"{success} purchase(s) recalculated successfully.",
                messages.SUCCESS,
            )

        if failed:
            self.message_user(
                request,
                (
                    f"{failed} purchase(s) failed validation. "
                    "Check GST / Non-GST settings."
                ),
                messages.ERROR,
            )

    @admin.action(description="Refresh payment summaries")
    def refresh_payment_summaries(self, request, queryset):

        count = 0

        for purchase in queryset:
            purchase.update_payment_summary()
            count += 1

        self.message_user(
            request,
            f"Payment summary refreshed for {count} purchase(s).",
            messages.SUCCESS,
        )

    actions = (
        "mark_confirmed",
        "mark_received",
        "mark_cancelled",
        "recalculate_amounts",
        "refresh_payment_summaries",
    )




# =========================================================
# PURCHASE PAYMENT INSTALLMENT ADMIN
# =========================================================

@admin.register(PurchasePaymentInstallment)
class PurchasePaymentInstallmentAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "purchase",
                "purchase__party",
                "payment_method",
            )
        )

    list_display = (
        "purchase_display",
        "party_display",
        "installment_number_display",
        "due_date",
        "installment_amount_display",
        "paid_amount_display",
        "remaining_amount_display",
        "payment_method_display",
        "payment_date",
        "status_badge",
    )

    search_fields = (
        "purchase__purchase_number",
        "purchase__invoice_number",
        "purchase__party__name",
        "purchase__party__contact_person",
        "purchase__party__phone",
        "purchase__party__email",
        "purchase__party__gst_number",
        "transaction_reference",
        "payment_method__name",
    )

    list_filter = (
        "status",
        "payment_method",
        "due_date",
        "payment_date",
    )

    date_hierarchy = "due_date"

    ordering = (
        "due_date",
        "installment_number",
    )

    list_per_page = 25

    autocomplete_fields = (
        "purchase",
        "payment_method",
    )

    readonly_fields = (
        "remaining_amount",
        "status",
        "installment_summary",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Installment Information",
            {
                "fields": (
                    "purchase",
                    "installment_number",
                    "due_date",
                    "installment_amount",
                ),
            },
        ),

        (
            "Payment Information",
            {
                "fields": (
                    "paid_amount",
                    "remaining_amount",
                    "payment_method",
                    "payment_date",
                    "transaction_reference",
                    "status",
                ),
            },
        ),

        (
            "Installment Summary",
            {
                "fields": (
                    "installment_summary",
                ),
            },
        ),

        (
            "Notes",
            {
                "fields": (
                    "notes",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    # =====================================================
    # PURCHASE
    # =====================================================

    @admin.display(
        description="Purchase",
        ordering="purchase__purchase_number",
    )
    def purchase_display(self, obj):

        if not obj or not obj.purchase:
            return "-"

        return format_html(
            "<strong>{}</strong>",
            obj.purchase.purchase_number,
        )

    # =====================================================
    # PARTY
    # =====================================================

    @admin.display(
        description="Party",
        ordering="purchase__party__name",
    )
    def party_display(self, obj):

        if not obj or not obj.purchase or not obj.purchase.party:
            return "-"

        return obj.purchase.party.name

    # =====================================================
    # INSTALLMENT NUMBER
    # =====================================================

    @admin.display(
        description="Installment",
        ordering="installment_number",
    )
    def installment_number_display(self, obj):

        return format_html(
            "<strong>#{}</strong>",
            obj.installment_number,
        )

    # =====================================================
    # INSTALLMENT AMOUNT
    # =====================================================

    @admin.display(
        description="Amount",
        ordering="installment_amount",
    )
    def installment_amount_display(self, obj):

        amount = money(obj.installment_amount)

        return format_html(
            "<strong>₹ {}</strong>",
            amount,
        )

    # =====================================================
    # PAID AMOUNT
    # =====================================================

    @admin.display(
        description="Paid",
        ordering="paid_amount",
    )
    def paid_amount_display(self, obj):

        amount = money(obj.paid_amount)

        return format_html(
            "<span style='color:#16a34a;font-weight:600;'>"
            "₹ {}"
            "</span>",
            amount,
        )

    # =====================================================
    # REMAINING AMOUNT
    # =====================================================

    @admin.display(
        description="Remaining",
        ordering="remaining_amount",
    )
    def remaining_amount_display(self, obj):

        remaining = (
            obj.remaining_amount
            or Decimal("0.00")
        )

        amount = money(remaining)

        if remaining > Decimal("0.00"):

            return format_html(
                "<strong style='color:#dc2626;'>"
                "₹ {}"
                "</strong>",
                amount,
            )

        return format_html(
            "<strong style='color:#16a34a;'>"
            "₹ {}"
            "</strong>",
            amount,
        )

    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    @admin.display(
        description="Payment Method",
        ordering="payment_method__name",
    )
    def payment_method_display(self, obj):

        if obj.payment_method:
            return obj.payment_method.name

        return format_html(
            "<span style='color:#9ca3af;'>{}</span>",
            "Not Added",
        )

    # =====================================================
    # STATUS
    # =====================================================

    @admin.display(
        description="Status",
        ordering="status",
    )
    def status_badge(self, obj):

        colors = {
            "PENDING": "#dc2626",
            "PARTIAL": "#f59e0b",
            "PAID": "#16a34a",
            "CANCELLED": "#6b7280",
        }

        color = colors.get(
            obj.status,
            "#6b7280",
        )

        return format_html(
            "<span style='"
            "background:{};"
            "color:white;"
            "padding:5px 10px;"
            "border-radius:15px;"
            "font-size:11px;"
            "font-weight:600;"
            "'>{}</span>",
            color,
            obj.get_status_display(),
        )

    # =====================================================
    # INSTALLMENT SUMMARY
    # =====================================================

    @admin.display(
        description="Installment Summary",
    )
    def installment_summary(self, obj):

        if not obj:
            return "-"

        installment_amount = (
            obj.installment_amount
            or Decimal("0.00")
        )

        paid_amount = (
            obj.paid_amount
            or Decimal("0.00")
        )

        remaining_amount = (
            obj.remaining_amount
            or Decimal("0.00")
        )

        percentage = Decimal("0.00")

        if installment_amount > Decimal("0.00"):

            percentage = (
                paid_amount / installment_amount
            ) * Decimal("100")

        installment_amount_text = money(
            installment_amount
        )

        paid_amount_text = money(
            paid_amount
        )

        remaining_amount_text = money(
            remaining_amount
        )

        percentage_text = f"{percentage:.2f}"

        purchase_number = (
            obj.purchase.purchase_number
            if obj.purchase
            else "-"
        )

        party_name = (
            obj.purchase.party.name
            if obj.purchase and obj.purchase.party
            else "-"
        )

        payment_method = (
            obj.payment_method.name
            if obj.payment_method
            else "-"
        )

        return format_html(
            """
            <div style="
                background:#f8fafc;
                border:1px solid #e2e8f0;
                border-radius:10px;
                padding:18px;
                max-width:650px;
                line-height:1.8;
            ">

                <h3>Installment #{}</h3>

                <p>
                    <strong>Purchase:</strong>
                    {}
                </p>

                <p>
                    <strong>Party:</strong>
                    {}
                </p>

                <p>
                    <strong>Due Date:</strong>
                    {}
                </p>

                <hr>

                <p>
                    <strong>Installment Amount:</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>Paid:</strong>
                    <span style="
                        color:#16a34a;
                        font-weight:600;
                    ">
                        ₹ {}
                    </span>
                </p>

                <p>
                    <strong>Remaining:</strong>
                    <span style="
                        color:#dc2626;
                        font-weight:600;
                    ">
                        ₹ {}
                    </span>
                </p>

                <p>
                    <strong>Payment Progress:</strong>
                    {}%
                </p>

                <p>
                    <strong>Payment Method:</strong>
                    {}
                </p>

                <p>
                    <strong>Payment Date:</strong>
                    {}
                </p>

                <p>
                    <strong>Transaction Reference:</strong>
                    {}
                </p>

            </div>
            """,
            obj.installment_number,
            purchase_number,
            party_name,
            obj.due_date,
            installment_amount_text,
            paid_amount_text,
            remaining_amount_text,
            percentage_text,
            payment_method,
            obj.payment_date or "-",
            obj.transaction_reference or "-",
        )

    # =====================================================
    # ACTION
    # =====================================================

    @admin.action(
        description="Cancel selected installments"
    )
    def mark_cancelled(self, request, queryset):

        queryset.update(
            status=PurchasePaymentInstallment.Status.CANCELLED
        )

    actions = (
        "mark_cancelled",
    )