from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.master.models import BaseModel


# =========================================================
# PARTY
# =========================================================

class Party(BaseModel):

    class PartyType(models.TextChoices):
        MANUFACTURER = "MANUFACTURER", "Manufacturer"
        WHOLESALER = "WHOLESALER", "Wholesaler"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"
        OTHER = "OTHER", "Other"

    # ---------------------------------------------------------
    # PERSONAL / PARTY DETAILS
    # ---------------------------------------------------------

    name = models.CharField(
        max_length=200,
        db_index=True,
    )

    party_type = models.CharField(
        max_length=30,
        choices=PartyType.choices,
        default=PartyType.OTHER,
        db_index=True,
    )

    contact_person = models.CharField(
        max_length=150,
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
    )

    gpay_number = models.CharField(
        max_length=20,
        blank=True,
    )

    # ---------------------------------------------------------
    # GST DETAILS
    # ---------------------------------------------------------

    gst_number = models.CharField(
        max_length=15,
        blank=True,
        db_index=True,
    )

    # ---------------------------------------------------------
    # BANK DETAILS
    # ---------------------------------------------------------

    bank_name = models.CharField(
        max_length=150,
        blank=True,
    )

    account_holder_name = models.CharField(
        max_length=200,
        blank=True,
    )

    account_number = models.CharField(
        max_length=50,
        blank=True,
    )

    ifsc_code = models.CharField(
        max_length=20,
        blank=True,
    )

    branch_name = models.CharField(
        max_length=150,
        blank=True,
    )

    upi_id = models.CharField(
        max_length=100,
        blank=True,
    )

    # ---------------------------------------------------------
    # NOTES
    # ---------------------------------------------------------

    notes = models.TextField(
        blank=True,
    )

    class Meta:
        db_table = "parties"
        ordering = ["name"]

        verbose_name = "Party"
        verbose_name_plural = "Parties"

    def __str__(self):
        return self.name


# =========================================================
# PARTY PAYMENT QR
# =========================================================

class PartyPaymentQR(BaseModel):

    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="payment_qrs",
    )

    qr_name = models.CharField(
        max_length=100,
        help_text="Example: HDFC QR, G-Pay QR, PhonePe QR",
    )

    qr_image = models.ImageField(
        upload_to="parties/payment_qr/",
    )

    upi_id = models.CharField(
        max_length=100,
        blank=True,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "party_payment_qrs"

        ordering = [
            "-is_primary",
            "qr_name",
        ]

        verbose_name = "Party Payment QR"
        verbose_name_plural = "Party Payment QRs"

    def __str__(self):
        return f"{self.party.name} - {self.qr_name}"


# =========================================================
# PAYMENT METHOD
# =========================================================

class PaymentMethod(BaseModel):

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        db_table = "payment_methods"

        ordering = ["name"]

        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return self.name


# =========================================================
# PARTY ORDER
# =========================================================

class PartyOrder(BaseModel):

    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class TaxType(models.TextChoices):
        GST = "GST", "GST"
        NON_GST = "NON_GST", "Non-GST"

    # ---------------------------------------------------------
    # PARTY
    # ---------------------------------------------------------

    party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="orders",
        db_index=True,
    )

    # ---------------------------------------------------------
    # ORDER INFORMATION
    # ---------------------------------------------------------

    order_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
    )

    order_date = models.DateField(
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )

    # ---------------------------------------------------------
    # GST
    # ---------------------------------------------------------

    tax_type = models.CharField(
        max_length=20,
        choices=TaxType.choices,
        default=TaxType.NON_GST,
        db_index=True,
    )

    gst_number = models.CharField(
        max_length=15,
        blank=True,
    )

    # ---------------------------------------------------------
    # AMOUNT
    # ---------------------------------------------------------

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    cgst_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    sgst_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    igst_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    other_charges = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # ---------------------------------------------------------
    # NOTES
    # ---------------------------------------------------------

    notes = models.TextField(
        blank=True,
    )

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------

    class Meta:
        db_table = "party_orders"

        ordering = [
            "-order_date",
            "-created_at",
        ]

        verbose_name = "Party Order"
        verbose_name_plural = "Party Orders"

        indexes = [
            models.Index(
                fields=["party", "order_date"],
                name="party_order_party_date_idx",
            ),
            models.Index(
                fields=["status", "order_date"],
                name="party_order_status_date_idx",
            ),
        ]

    # ---------------------------------------------------------
    # STRING
    # ---------------------------------------------------------

    def __str__(self):
        return self.order_number

    # ---------------------------------------------------------
    # GST
    # ---------------------------------------------------------

    @property
    def total_gst(self):
        return (
            self.cgst_amount
            + self.sgst_amount
            + self.igst_amount
        )

    # ---------------------------------------------------------
    # PAYMENT SUMMARY
    # ---------------------------------------------------------

    @property
    def total_paid(self):
        """
        Total amount successfully paid against this order.
        """

        return (
            self.payments
            .filter(
                status=Payment.PaymentStatus.COMPLETED,
                is_active=True,
            )
            .aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

    @property
    def outstanding_amount(self):
        """
        Remaining amount to be paid.
        """

        outstanding = self.total_amount - self.total_paid

        if outstanding < Decimal("0.00"):
            return Decimal("0.00")

        return outstanding

    @property
    def payment_status(self):

        if self.total_amount <= Decimal("0.00"):
            return "NO_AMOUNT"

        if self.total_paid <= Decimal("0.00"):
            return "UNPAID"

        if self.total_paid >= self.total_amount:
            return "PAID"

        return "PARTIALLY_PAID"

    # ---------------------------------------------------------
    # AUTOMATIC ORDER NUMBER
    # ---------------------------------------------------------

    def save(self, *args, **kwargs):

        if not self.order_number:

            prefix = "YL\\SUP\\ORD\\"

            last_order = (
                PartyOrder.objects
                .filter(
                    order_number__startswith=prefix
                )
                .order_by("-created_at")
                .first()
            )

            if last_order and last_order.order_number:

                try:
                    last_number = int(
                        last_order.order_number.split("\\")[-1]
                    )

                    next_number = last_number + 1

                except (ValueError, AttributeError):

                    next_number = 1

            else:

                next_number = 1

            self.order_number = (
                f"{prefix}{next_number:06d}"
            )

        super().save(*args, **kwargs)


# =========================================================
# PAYMENT
# =========================================================

class Payment(BaseModel):

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    # ---------------------------------------------------------
    # ORDER
    # ---------------------------------------------------------

    order = models.ForeignKey(
        PartyOrder,
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True,
    )

    # ---------------------------------------------------------
    # PAYMENT INFORMATION
    # ---------------------------------------------------------

    payment_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
    )

    payment_date = models.DateField(
        db_index=True,
    )

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name="payments",
        db_index=True,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.COMPLETED,
        db_index=True,
    )

    # ---------------------------------------------------------
    # TRANSACTION DETAILS
    # ---------------------------------------------------------

    transaction_reference = models.CharField(
        max_length=150,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    # ---------------------------------------------------------
    # META
    # ---------------------------------------------------------

    class Meta:
        db_table = "payments"

        ordering = [
            "-payment_date",
            "-created_at",
        ]

        verbose_name = "Payment"
        verbose_name_plural = "Payments"

        indexes = [
            models.Index(
                fields=["order", "payment_date"],
                name="payment_order_date_idx",
            ),
            models.Index(
                fields=["status", "payment_date"],
                name="payment_status_date_idx",
            ),
        ]

    # ---------------------------------------------------------
    # STRING
    # ---------------------------------------------------------

    def __str__(self):
        return self.payment_number

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    def clean(self):

        super().clean()

        if self.amount is None:
            return

        if self.amount <= Decimal("0.00"):
            raise ValidationError({
                "amount": "Payment amount must be greater than zero."
            })

        if not self.order_id:
            return

        # Only completed payments affect the paid amount.
        if self.status != self.PaymentStatus.COMPLETED:
            return

        existing_paid = (
            Payment.objects
            .filter(
                order=self.order,
                status=self.PaymentStatus.COMPLETED,
                is_active=True,
            )
            .exclude(pk=self.pk)
            .aggregate(
                total=models.Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        remaining_amount = (
            self.order.total_amount - existing_paid
        )

        if self.amount > remaining_amount:
            raise ValidationError({
                "amount": (
                    f"Payment cannot exceed the outstanding "
                    f"amount of ₹{remaining_amount:.2f}."
                )
            })

    # ---------------------------------------------------------
    # AUTOMATIC PAYMENT NUMBER
    # ---------------------------------------------------------

    def save(self, *args, **kwargs):

        self.full_clean()

        if not self.payment_number:

            prefix = "YL\\SUP\\PAY\\"

            last_payment = (
                Payment.objects
                .filter(
                    payment_number__startswith=prefix
                )
                .order_by("-created_at")
                .first()
            )

            if last_payment and last_payment.payment_number:

                try:
                    last_number = int(
                        last_payment.payment_number.split("\\")[-1]
                    )

                    next_number = last_number + 1

                except (ValueError, AttributeError):

                    next_number = 1

            else:

                next_number = 1

            self.payment_number = (
                f"{prefix}{next_number:06d}"
            )

        super().save(*args, **kwargs)