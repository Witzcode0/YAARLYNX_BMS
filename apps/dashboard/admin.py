from decimal import Decimal

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Party,
    PartyPaymentQR,
    PaymentMethod,
    PartyPurchase,
    PurchasePaymentInstallment,
)


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

@admin.register(PartyPurchase)
class PartyPurchaseAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("party")
        )

    list_display = (
        "purchase_number_display",
        "party_display",
        "purchase_date",
        "invoice_number_display",
        "grand_total_display",
        "paid_amount_display",
        "due_amount_display",
        "status_badge",
        "payment_status_badge",
    )

    search_fields = (
        "purchase_number",
        "invoice_number",
        "party__name",
        "party__contact_person",
        "party__phone",
        "party__alternate_phone",
        "party__email",
        "party__gst_number",
    )

    list_filter = (
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

    list_per_page = 25

    autocomplete_fields = (
        "party",
    )

    inlines = (
        PurchasePaymentInstallmentInline,
    )

    readonly_fields = (
        "purchase_number_display",

        # Automatic purchase calculations
        "discount_amount",
        "taxable_amount",
        "cgst_amount",
        "sgst_amount",
        "igst_amount",
        "round_off",
        "grand_total",

        # Automatic payment calculations
        "paid_amount_display",
        "due_amount_display",
        "payment_status_display",

        "purchase_summary",
        "payment_summary",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Purchase Information",
            {
                "fields": (
                    "purchase_number_display",
                    "party",
                    "purchase_date",
                    "status",
                ),
            },
        ),

        (
            "Supplier Invoice",
            {
                "fields": (
                    "invoice_number",
                    "invoice_date",
                ),
            },
        ),

        (
            "Purchase Amount",
            {
                "fields": (
                    "subtotal",
                    "discount_percent",
                    "discount_amount",
                    "taxable_amount",
                ),
                "description": (
                    "Enter Subtotal and Discount %. "
                    "Discount Amount and Taxable Amount are calculated automatically."
                ),
            },
        ),

        (
            "GST / Tax",
            {
                "fields": (
                    "cgst_percent",
                    "cgst_amount",
                    "sgst_percent",
                    "sgst_amount",
                    "igst_percent",
                    "igst_amount",
                ),
                "description": (
                    "Enter GST percentages. GST amounts are calculated automatically "
                    "from the taxable amount. Use either CGST + SGST or IGST."
                ),
            },
        ),

        (
            "Additional Charges & Total",
            {
                "fields": (
                    "other_charges",
                    "round_off",
                    "grand_total",
                ),
                "description": (
                    "Grand Total is calculated automatically from taxable amount, "
                    "GST, other charges and round-off."
                ),
            },
        ),

        (
            "Payment Information",
            {
                "fields": (
                    "paid_amount_display",
                    "due_amount_display",
                    "payment_status_display",
                    "payment_summary",
                ),
            },
        ),

        (
            "Purchase Summary",
            {
                "fields": (
                    "purchase_summary",
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
    # AUTOMATIC CALCULATION
    # =====================================================
    # Source fields entered by admin:
    #   subtotal, discount_percent, cgst_percent,
    #   sgst_percent, igst_percent, other_charges
    #
    # Automatically calculated by PartyPurchase model:
    #   discount_amount, taxable_amount,
    #   cgst_amount, sgst_amount, igst_amount,
    #   round_off, grand_total
    #
    # Payment is calculated from PurchasePaymentInstallment:
    #   paid_amount, due_amount, payment_status
    #
    # =====================================================
    # PURCHASE NUMBER
    # =====================================================

    @admin.display(
        description="Purchase Number",
        ordering="purchase_number",
    )
    def purchase_number_display(self, obj):

        if not obj:
            return "Will be generated automatically"

        if not obj.purchase_number:
            return format_html(
                "<span style='color:#9ca3af;'>{}</span>",
                "Will be generated automatically",
            )

        return format_html(
            """
            <div style="
                display:inline-block;
                background:#f1f5f9;
                border:1px solid #cbd5e1;
                border-radius:8px;
                padding:8px 14px;
                font-family:monospace;
                font-size:14px;
                font-weight:700;
                color:#0f172a;
                letter-spacing:0.3px;
            ">
                {}
            </div>
            """,
            obj.purchase_number,
        )

    # =====================================================
    # PARTY
    # =====================================================

    @admin.display(
        description="Party",
        ordering="party__name",
    )
    def party_display(self, obj):

        if not obj or not obj.party:
            return "-"

        return format_html(
            "<strong>{}</strong><br>"
            "<small>{}</small>",
            obj.party.name,
            obj.party.phone or "-",
        )

    # =====================================================
    # INVOICE
    # =====================================================

    @admin.display(
        description="Invoice No.",
        ordering="invoice_number",
    )
    def invoice_number_display(self, obj):

        if obj.invoice_number:
            return obj.invoice_number

        return format_html(
            "<span style='color:#9ca3af;'>{}</span>",
            "Not Added",
        )

    # =====================================================
    # GRAND TOTAL
    # =====================================================

    @admin.display(
        description="Grand Total",
        ordering="grand_total",
    )
    def grand_total_display(self, obj):

        amount = money(obj.grand_total)

        return format_html(
            "<strong>₹ {}</strong>",
            amount,
        )

    # =====================================================
    # PAID
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
    # DUE
    # =====================================================

    @admin.display(
        description="Due",
        ordering="due_amount",
    )
    def due_amount_display(self, obj):

        due = obj.due_amount or Decimal("0.00")

        amount = money(due)

        if due > Decimal("0.00"):

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
    # PAYMENT STATUS DISPLAY
    # =====================================================

    @admin.display(
        description="Payment Status",
        ordering="payment_status",
    )
    def payment_status_display(self, obj):

        if not obj:
            return "-"

        colors = {
            "UNPAID": "#dc2626",
            "PARTIAL": "#f59e0b",
            "PAID": "#16a34a",
        }

        color = colors.get(
            obj.payment_status,
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
            obj.get_payment_status_display(),
        )


    # =====================================================
    # PURCHASE STATUS
    # =====================================================

    @admin.display(
        description="Purchase Status",
        ordering="status",
    )
    def status_badge(self, obj):

        colors = {
            "DRAFT": "#6b7280",
            "CONFIRMED": "#2563eb",
            "RECEIVED": "#16a34a",
            "PARTIAL": "#f59e0b",
            "CANCELLED": "#dc2626",
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
    # PAYMENT STATUS
    # =====================================================

    @admin.display(
        description="Payment",
        ordering="payment_status",
    )
    def payment_status_badge(self, obj):

        colors = {
            "UNPAID": "#dc2626",
            "PARTIAL": "#f59e0b",
            "PAID": "#16a34a",
        }

        color = colors.get(
            obj.payment_status,
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
            obj.get_payment_status_display(),
        )

    # =====================================================
    # PURCHASE SUMMARY
    # =====================================================

    @admin.display(
        description="Purchase Summary",
    )
    def purchase_summary(self, obj):

        if not obj:
            return "-"

        subtotal = money(obj.subtotal)
        discount_percent = f"{Decimal(obj.discount_percent or 0):.2f}"
        discount = money(obj.discount_amount)
        taxable = money(obj.taxable_amount)

        cgst_percent = f"{Decimal(obj.cgst_percent or 0):.2f}"
        cgst = money(obj.cgst_amount)

        sgst_percent = f"{Decimal(obj.sgst_percent or 0):.2f}"
        sgst = money(obj.sgst_amount)

        igst_percent = f"{Decimal(obj.igst_percent or 0):.2f}"
        igst = money(obj.igst_amount)

        other_charges = money(obj.other_charges)
        round_off = money(obj.round_off)
        grand_total = money(obj.grand_total)

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

                <h3 style="margin-top:0;">
                    Purchase Summary
                </h3>

                <p>
                    <strong>Purchase No:</strong>
                    {}
                </p>

                <p>
                    <strong>Party:</strong>
                    {}
                </p>

                <p>
                    <strong>Date:</strong>
                    {}
                </p>

                <p>
                    <strong>Invoice:</strong>
                    {}
                </p>

                <hr>

                <p>
                    <strong>Subtotal:</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>Discount ({}%):</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>Taxable:</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>CGST ({}%):</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>SGST ({}%):</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>IGST ({}%):</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>Other Charges:</strong>
                    ₹ {}
                </p>

                <p>
                    <strong>Round Off:</strong>
                    ₹ {}
                </p>

                <hr>

                <p style="
                    font-size:17px;
                    font-weight:700;
                    margin-bottom:0;
                ">
                    Grand Total:
                    ₹ {}
                </p>

            </div>
            """,
            obj.purchase_number or "-",
            obj.party.name if obj.party else "-",
            obj.purchase_date,
            obj.invoice_number or "-",
            subtotal,
            discount_percent,
            discount,
            taxable,
            cgst_percent,
            cgst,
            sgst_percent,
            sgst,
            igst_percent,
            igst,
            other_charges,
            round_off,
            grand_total,
        )

    # =====================================================
    # PAYMENT SUMMARY
    # =====================================================

    @admin.display(
        description="Payment Summary",
    )
    def payment_summary(self, obj):

        if not obj:
            return "-"

        installments = obj.installments.all()

        total = installments.count()

        paid = installments.filter(
            status=PurchasePaymentInstallment.Status.PAID
        ).count()

        partial = installments.filter(
            status=PurchasePaymentInstallment.Status.PARTIAL
        ).count()

        pending = installments.filter(
            status=PurchasePaymentInstallment.Status.PENDING
        ).count()

        cancelled = installments.filter(
            status=PurchasePaymentInstallment.Status.CANCELLED
        ).count()

        grand_total = money(obj.grand_total)
        paid_amount = money(obj.paid_amount)
        due_amount = money(obj.due_amount)

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

                <h3 style="margin-top:0;">
                    Payment Summary
                </h3>

                <p>
                    <strong>Grand Total:</strong>
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
                    <strong>Due:</strong>
                    <span style="
                        color:#dc2626;
                        font-weight:600;
                    ">
                        ₹ {}
                    </span>
                </p>

                <hr>

                <p>
                    <strong>Total Installments:</strong>
                    {}
                </p>

                <p>
                    <strong>Paid Installments:</strong>
                    <span style="color:#16a34a;">
                        {}
                    </span>
                </p>

                <p>
                    <strong>Partial:</strong>
                    <span style="color:#f59e0b;">
                        {}
                    </span>
                </p>

                <p>
                    <strong>Pending:</strong>
                    <span style="color:#dc2626;">
                        {}
                    </span>
                </p>

                <p>
                    <strong>Cancelled:</strong>
                    {}
                </p>

            </div>
            """,
            grand_total,
            paid_amount,
            due_amount,
            total,
            paid,
            partial,
            pending,
            cancelled,
        )

    # =====================================================
    # ACTIONS
    # =====================================================

    @admin.action(
        description="Recalculate selected purchase totals & payments"
    )
    def recalculate_selected_purchases(self, request, queryset):

        updated = 0

        for purchase in queryset:

            # Re-run subtotal/discount/GST/charges calculation.
            purchase.calculate_amounts()

            # Persist calculated purchase amounts without touching
            # the editable source fields.
            PartyPurchase.objects.filter(
                pk=purchase.pk
            ).update(
                discount_amount=purchase.discount_amount,
                taxable_amount=purchase.taxable_amount,
                cgst_amount=purchase.cgst_amount,
                sgst_amount=purchase.sgst_amount,
                igst_amount=purchase.igst_amount,
                round_off=purchase.round_off,
                grand_total=purchase.grand_total,
            )

            # Recalculate payment summary from installments.
            purchase.update_payment_summary()

            updated += 1

        self.message_user(
            request,
            f"{updated} purchase(s) recalculated successfully.",
        )


    @admin.action(
        description="Mark selected purchases as Confirmed"
    )
    def mark_confirmed(self, request, queryset):

        queryset.update(
            status=PartyPurchase.Status.CONFIRMED
        )

    @admin.action(
        description="Mark selected purchases as Received"
    )
    def mark_received(self, request, queryset):

        queryset.update(
            status=PartyPurchase.Status.RECEIVED
        )

    @admin.action(
        description="Mark selected purchases as Cancelled"
    )
    def mark_cancelled(self, request, queryset):

        queryset.update(
            status=PartyPurchase.Status.CANCELLED
        )

    actions = (
        "recalculate_selected_purchases",
        "mark_confirmed",
        "mark_received",
        "mark_cancelled",
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