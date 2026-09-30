from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.master.models import BaseModel
from apps.accounts.models import UserAccount

from apps.master.utils import get_instance_file_path
from apps.master.mixins import FileReplaceMixin


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
        db_index=True
    )

    party_type = models.CharField(
        max_length=30,
        choices=PartyType.choices,
        default=PartyType.OTHER,
        db_index=True
    )

    contact_person = models.CharField(
        max_length=150,
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    alternate_phone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    pincode = models.CharField(
        max_length=10,
        blank=True
    )

    gpay_number = models.CharField(
        max_length=20,
        blank=True
    )

    # ---------------------------------------------------------
    # GST DETAILS
    # ---------------------------------------------------------

    gst_number = models.CharField(
        max_length=15,
        blank=True,
        db_index=True
    )

    # ---------------------------------------------------------
    # BANK DETAILS
    # ---------------------------------------------------------

    bank_name = models.CharField(
        max_length=150,
        blank=True
    )

    account_holder_name = models.CharField(
        max_length=200,
        blank=True
    )

    account_number = models.CharField(
        max_length=50,
        blank=True
    )

    ifsc_code = models.CharField(
        max_length=20,
        blank=True
    )

    branch_name = models.CharField(
        max_length=150,
        blank=True
    )

    upi_id = models.CharField(
        max_length=100,
        blank=True
    )

    # ---------------------------------------------------------
    # NOTES
    # ---------------------------------------------------------

    notes = models.TextField(
        blank=True
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

def party_payment_qr_upload_path(instance, filename):
    return get_instance_file_path(
        "parties/payment_qr",
        instance,
        filename
    )


class PartyPaymentQR(
    FileReplaceMixin,
    BaseModel
):

    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="payment_qrs"
    )

    qr_name = models.CharField(
        max_length=100,
        help_text="Example: HDFC QR, G-Pay QR, PhonePe QR"
    )

    qr_image = models.ImageField(
        upload_to=party_payment_qr_upload_path
    )

    upi_id = models.CharField(
        max_length=100,
        blank=True
    )

    is_primary = models.BooleanField(
        default=False
    )

    # ---------------------------------------------------------
    # FILE MANAGEMENT
    # ---------------------------------------------------------

    file_fields = [
        "qr_image",
    ]

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
        unique=True
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    class Meta:
        db_table = "payment_methods"
        ordering = ["name"]
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"

    def __str__(self):
        return self.name


# =========================================================
# PARTY PURCHASE ORDER
# =========================================================

def party_purchase_invoice_upload_path(instance, filename):
    return get_instance_file_path(
        "party_bills",
        instance,
        filename
    )


class PartyPurchase(
    FileReplaceMixin,
    BaseModel
):

    # =========================================================
    # PURCHASE STATUS
    # =========================================================

    class Status(models.TextChoices):

        DRAFT = "DRAFT", "Draft"

        CONFIRMED = "CONFIRMED", "Confirmed"

        RECEIVED = "RECEIVED", "Received"

        PARTIAL = "PARTIAL", "Partially Received"

        CANCELLED = "CANCELLED", "Cancelled"

    # =========================================================
    # PAYMENT STATUS
    # =========================================================

    class PaymentStatus(models.TextChoices):

        UNPAID = "UNPAID", "Unpaid"

        PARTIAL = "PARTIAL", "Partially Paid"

        PAID = "PAID", "Paid"

    # =========================================================
    # BILL TYPE
    # =========================================================

    class BillType(models.TextChoices):

        GST = "GST", "GST Bill"

        NON_GST = "NON_GST", "Non-GST Bill"

    # =========================================================
    # PURCHASE DETAILS
    # =========================================================

    purchase_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        blank=True,
        editable=False
    )

    party = models.ForeignKey(
        "Party",
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    purchase_date = models.DateField()

    # =========================================================
    # SUPPLIER INVOICE
    # =========================================================

    invoice_number = models.CharField(
        max_length=100,
        blank=True
    )

    invoice_date = models.DateField(
        null=True,
        blank=True
    )

    # =========================================================
    # BILL TYPE
    # =========================================================

    bill_type = models.CharField(
        max_length=10,
        choices=BillType.choices,
        default=BillType.GST,
        db_index=True,
        help_text="Select whether this is a GST or Non-GST bill."
    )

    # =========================================================
    # BILL DOCUMENT
    # =========================================================

    invoice_document = models.FileField(
        upload_to=party_purchase_invoice_upload_path,
        blank=True,
        null=True,
        help_text="Upload supplier GST/Non-GST bill image or PDF."
    )

    # ---------------------------------------------------------
    # FILE MANAGEMENT
    # ---------------------------------------------------------

    file_fields = [
        "invoice_document",
    ]

    # =========================================================
    # PURCHASE STATUS
    # =========================================================

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
        editable=False
    )

    # =========================================================
    # BASIC AMOUNT
    # =========================================================

    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # =========================================================
    # DISCOUNT
    # =========================================================

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Enter discount percentage."
    )

    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # TAXABLE AMOUNT
    # =========================================================

    taxable_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # CGST
    # =========================================================

    cgst_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Enter CGST percentage."
    )

    cgst_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # SGST
    # =========================================================

    sgst_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Enter SGST percentage."
    )

    sgst_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # IGST
    # =========================================================

    igst_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Enter IGST percentage."
    )

    igst_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # OTHER CHARGES
    # =========================================================

    other_charges = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Transport, packing, shipping, etc."
    )

    # =========================================================
    # ROUND OFF
    # =========================================================

    round_off = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # GRAND TOTAL
    # =========================================================

    grand_total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # PAYMENT SUMMARY
    # =========================================================

    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    due_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # NOTES
    # =========================================================

    notes = models.TextField(
        blank=True
    )

    # =========================================================
    # META
    # =========================================================

    class Meta:
        db_table = "party_purchases"

        ordering = [
            "-purchase_date",
            "-created_at",
        ]

        verbose_name = "Party Purchase"
        verbose_name_plural = "Party Purchases"

    # =========================================================
    # STRING
    # =========================================================

    def __str__(self):
        return (
            f"{self.purchase_number} - "
            f"{self.party.name}"
        )

    # =========================================================
    # PURCHASE NUMBER
    # =========================================================

    def generate_purchase_number(self):

        return (
            f"BO/SUP/"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

    # =========================================================
    # DECIMAL HELPER
    # =========================================================

    @staticmethod
    def decimal(value):

        if value is None:
            return Decimal("0.00")

        return Decimal(value)

    # =========================================================
    # CALCULATE PURCHASE AMOUNTS
    # =========================================================

    def calculate_amounts(self):

        # -----------------------------------------------------
        # BASIC VALUES
        # -----------------------------------------------------

        subtotal = self.decimal(
            self.subtotal
        )

        discount_percent = self.decimal(
            self.discount_percent
        )

        cgst_percent = self.decimal(
            self.cgst_percent
        )

        sgst_percent = self.decimal(
            self.sgst_percent
        )

        igst_percent = self.decimal(
            self.igst_percent
        )

        other_charges = self.decimal(
            self.other_charges
        )

        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------

        if subtotal < Decimal("0.00"):

            raise ValidationError(
                "Subtotal cannot be negative."
            )

        if discount_percent < Decimal("0.00"):

            raise ValidationError(
                "Discount percentage cannot be negative."
            )

        if discount_percent > Decimal("100.00"):

            raise ValidationError(
                "Discount percentage cannot be greater than 100%."
            )

        for name, value in (
            ("CGST", cgst_percent),
            ("SGST", sgst_percent),
            ("IGST", igst_percent),
        ):

            if value < Decimal("0.00"):

                raise ValidationError(
                    f"{name} percentage cannot be negative."
                )

            if value > Decimal("100.00"):

                raise ValidationError(
                    f"{name} percentage cannot be greater than 100%."
                )

        if other_charges < Decimal("0.00"):

            raise ValidationError(
                "Other charges cannot be negative."
            )

        # -----------------------------------------------------
        # NON-GST BILL
        # -----------------------------------------------------

        if self.bill_type == self.BillType.NON_GST:

            cgst_percent = Decimal("0.00")
            sgst_percent = Decimal("0.00")
            igst_percent = Decimal("0.00")

        # -----------------------------------------------------
        # GST BILL
        # -----------------------------------------------------

        elif self.bill_type == self.BillType.GST:

            # IGST cannot be combined with CGST / SGST

            if (
                cgst_percent > Decimal("0.00")
                or sgst_percent > Decimal("0.00")
            ):

                if igst_percent > Decimal("0.00"):

                    raise ValidationError(
                        "Use either CGST/SGST or IGST. "
                        "Do not use IGST together with CGST/SGST."
                    )

        # -----------------------------------------------------
        # DISCOUNT AMOUNT
        # -----------------------------------------------------

        discount_amount = (
            subtotal
            * discount_percent
            / Decimal("100")
        )

        discount_amount = discount_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # TAXABLE AMOUNT
        # -----------------------------------------------------

        taxable_amount = (
            subtotal - discount_amount
        )

        if taxable_amount < Decimal("0.00"):
            taxable_amount = Decimal("0.00")

        taxable_amount = taxable_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # CGST
        # -----------------------------------------------------

        cgst_amount = (
            taxable_amount
            * cgst_percent
            / Decimal("100")
        )

        cgst_amount = cgst_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # SGST
        # -----------------------------------------------------

        sgst_amount = (
            taxable_amount
            * sgst_percent
            / Decimal("100")
        )

        sgst_amount = sgst_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # IGST
        # -----------------------------------------------------

        igst_amount = (
            taxable_amount
            * igst_percent
            / Decimal("100")
        )

        igst_amount = igst_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # TOTAL BEFORE ROUND OFF
        # -----------------------------------------------------

        total_before_round = (
            taxable_amount
            + cgst_amount
            + sgst_amount
            + igst_amount
            + other_charges
        )

        total_before_round = total_before_round.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # ROUND OFF
        # -----------------------------------------------------

        rounded_total = total_before_round.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )

        round_off = (
            rounded_total
            - total_before_round
        )

        round_off = round_off.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # GRAND TOTAL
        # -----------------------------------------------------

        grand_total = (
            total_before_round
            + round_off
        )

        grand_total = grand_total.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        # -----------------------------------------------------
        # ASSIGN VALUES
        # -----------------------------------------------------

        self.discount_amount = discount_amount

        self.taxable_amount = taxable_amount

        self.cgst_amount = cgst_amount

        self.sgst_amount = sgst_amount

        self.igst_amount = igst_amount

        self.round_off = round_off

        self.grand_total = grand_total

    # =========================================================
    # PAYMENT CALCULATION
    # =========================================================

    def update_payment_summary(self):
        """
        Recalculate the purchase payment summary from installments.

        Source of truth:
            total paid = SUM(installments.paid_amount)
            due amount = grand_total - total paid

        This method never trusts the existing paid_amount/due_amount
        values on the purchase.
        """

        if not self.pk:
            return

        money_zero = Decimal("0.00")

        # -----------------------------------------------------
        # TOTAL PAID FROM ALL INSTALLMENTS
        # -----------------------------------------------------

        total_paid = (
            self.installments.aggregate(
                total=Sum("paid_amount")
            )["total"]
            or money_zero
        )

        total_paid = self.decimal(total_paid).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        grand_total = self.decimal(self.grand_total).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        # -----------------------------------------------------
        # REMAINING / DUE AMOUNT
        # -----------------------------------------------------

        due_amount = grand_total - total_paid

        # Never show a negative due amount.
        if due_amount < money_zero:
            due_amount = money_zero

        due_amount = due_amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        # -----------------------------------------------------
        # PAYMENT STATUS
        # -----------------------------------------------------

        if grand_total <= money_zero:
            payment_status = self.PaymentStatus.UNPAID

        elif total_paid >= grand_total:
            payment_status = self.PaymentStatus.PAID

        elif total_paid > money_zero:
            payment_status = self.PaymentStatus.PARTIAL

        else:
            payment_status = self.PaymentStatus.UNPAID

        # -----------------------------------------------------
        # UPDATE OBJECT
        # -----------------------------------------------------

        self.paid_amount = total_paid
        self.due_amount = due_amount
        self.payment_status = payment_status

        # -----------------------------------------------------
        # UPDATE DATABASE
        # -----------------------------------------------------

        PartyPurchase.objects.filter(
            pk=self.pk
        ).update(
            paid_amount=total_paid,
            due_amount=due_amount,
            payment_status=payment_status,
        )

    @property
    def total_installment_paid(self):
        """
        Actual total paid through all installments.
        """

        if not self.pk:
            return Decimal("0.00")

        total = (
            self.installments.aggregate(
                total=Sum("paid_amount")
            )["total"]
            or Decimal("0.00")
        )

        return self.decimal(total).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def remaining_payment_amount(self):
        """
        Actual amount still payable against this purchase.
        """

        grand_total = self.decimal(self.grand_total)
        total_paid = self.total_installment_paid

        remaining = grand_total - total_paid

        if remaining < Decimal("0.00"):
            remaining = Decimal("0.00")

        return remaining.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )


    # =========================================================
    # SAVE
    # =========================================================

    def save(self, *args, **kwargs):

        # -----------------------------------------------------
        # GENERATE PURCHASE NUMBER
        # -----------------------------------------------------

        if not self.purchase_number:

            self.purchase_number = (
                self.generate_purchase_number()
            )

        # -----------------------------------------------------
        # AUTOMATIC AMOUNT CALCULATION
        # -----------------------------------------------------

        self.calculate_amounts()

        # -----------------------------------------------------
        # NEW PURCHASE PAYMENT DEFAULT
        # -----------------------------------------------------

        if not self.pk:

            self.paid_amount = Decimal("0.00")

            self.due_amount = self.grand_total

            self.payment_status = (
                self.PaymentStatus.UNPAID
            )

        # -----------------------------------------------------
        # SAVE PURCHASE
        # -----------------------------------------------------

        super().save(*args, **kwargs)

        # -----------------------------------------------------
        # UPDATE PAYMENT FROM INSTALLMENTS
        # -----------------------------------------------------

        self.update_payment_summary()


# =========================================================
# PURCHASE PAYMENT INSTALLMENT
# =========================================================

class PurchasePaymentInstallment(BaseModel):

    # =========================================================
    # STATUS
    # =========================================================

    class Status(models.TextChoices):

        PENDING = "PENDING", "Pending"

        PAID = "PAID", "Paid"

        PARTIAL = "PARTIAL", "Partially Paid"

        CANCELLED = "CANCELLED", "Cancelled"

    # =========================================================
    # PURCHASE
    # =========================================================

    purchase = models.ForeignKey(
        PartyPurchase,
        on_delete=models.CASCADE,
        related_name="installments"
    )

    # =========================================================
    # INSTALLMENT DETAILS
    # =========================================================

    installment_number = models.PositiveIntegerField()

    due_date = models.DateField()

    # =========================================================
    # INSTALLMENT AMOUNT
    # =========================================================

    installment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    # =========================================================
    # PAYMENT
    # =========================================================

    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00")
    )

    remaining_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # =========================================================
    # PAYMENT METHOD
    # =========================================================

    payment_method = models.ForeignKey(
        "PaymentMethod",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_installments"
    )

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    transaction_reference = models.CharField(
        max_length=150,
        blank=True
    )

    # =========================================================
    # STATUS
    # =========================================================

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        editable=False
    )

    # =========================================================
    # NOTES
    # =========================================================

    notes = models.TextField(
        blank=True
    )

    # =========================================================
    # META
    # =========================================================

    class Meta:

        db_table = "purchase_payment_installments"

        ordering = [
            "installment_number",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "purchase",
                    "installment_number",
                ],
                name="unique_purchase_installment",
            )
        ]

        verbose_name = (
            "Purchase Payment Installment"
        )

        verbose_name_plural = (
            "Purchase Payment Installments"
        )

    # =========================================================
    # STRING
    # =========================================================

    def __str__(self):

        return (
            f"{self.purchase.purchase_number} - "
            f"Installment {self.installment_number}"
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    def clean(self):
        """
        Validate the installment and make sure cumulative payments
        never exceed the purchase grand total.
        """

        money_zero = Decimal("0.00")

        if self.installment_amount is None:
            raise ValidationError(
                "Installment amount is required."
            )

        self.installment_amount = Decimal(
            self.installment_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if self.installment_amount < money_zero:
            raise ValidationError(
                "Installment amount cannot be negative."
            )

        if self.paid_amount is None:
            self.paid_amount = money_zero

        self.paid_amount = Decimal(
            self.paid_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if self.paid_amount < money_zero:
            raise ValidationError(
                "Paid amount cannot be negative."
            )

        if self.paid_amount > self.installment_amount:
            raise ValidationError(
                "Paid amount cannot be greater than installment amount."
            )

        # -----------------------------------------------------
        # PURCHASE VALIDATION
        # -----------------------------------------------------

        if not self.purchase_id:
            return

        purchase = self.purchase

        existing_paid = (
            PurchasePaymentInstallment.objects
            .filter(
                purchase_id=self.purchase_id
            )
            .exclude(
                pk=self.pk
            )
            .aggregate(
                total=Sum("paid_amount")
            )["total"]
            or money_zero
        )

        existing_paid = Decimal(existing_paid).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        total_paid_after_save = (
            existing_paid + self.paid_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        grand_total = Decimal(
            purchase.grand_total
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if total_paid_after_save > grand_total:
            raise ValidationError(
                "Total installment payments cannot be greater "
                "than the purchase grand total."
            )

        # -----------------------------------------------------
        # INSTALLMENT REMAINING AMOUNT
        # -----------------------------------------------------

        self.remaining_amount = (
            self.installment_amount - self.paid_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )


    # =========================================================
    # SAVE
    # =========================================================

    def save(self, *args, **kwargs):
        # -----------------------------------------------------
        # RUN VALIDATION
        # -----------------------------------------------------

        self.full_clean()

        # -----------------------------------------------------
        # CALCULATE REMAINING AMOUNT
        # -----------------------------------------------------

        self.remaining_amount = (
            Decimal(self.installment_amount)
            - Decimal(self.paid_amount or Decimal("0.00"))
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if self.remaining_amount < Decimal("0.00"):
            self.remaining_amount = Decimal("0.00")

        # -----------------------------------------------------
        # PAYMENT STATUS
        # -----------------------------------------------------

        if self.paid_amount >= self.installment_amount:
            self.status = self.Status.PAID

        elif self.paid_amount > Decimal("0.00"):
            self.status = self.Status.PARTIAL

        else:
            self.status = self.Status.PENDING

        # -----------------------------------------------------
        # SAVE INSTALLMENT
        # -----------------------------------------------------

        super().save(*args, **kwargs)

        # -----------------------------------------------------
        # RECALCULATE PARENT PURCHASE
        # -----------------------------------------------------

        self.purchase.update_payment_summary()


    # =========================================================
    # DELETE
    # =========================================================

    def delete(self, *args, **kwargs):

        purchase = self.purchase

        result = super().delete(
            *args,
            **kwargs
        )

        # -----------------------------------------------------
        # RECALCULATE PARENT
        # -----------------------------------------------------

        if purchase and purchase.pk:

            purchase.update_payment_summary()

        return result


# =========================================================
# QUICK LINK CATEGORY
# =========================================================

class QuickLinkCategory(BaseModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:

        db_table = "quick_link_categories"

        ordering = [
            "display_order",
            "name",
        ]

        verbose_name = "Quick Link Category"
        verbose_name_plural = "Quick Link Categories"

    def __str__(self):
        return self.name


# =========================================================
# QUICK LINK
# =========================================================

class QuickLink(BaseModel):

    category = models.ForeignKey(
        QuickLinkCategory,
        on_delete=models.PROTECT,
        related_name="quick_links"
    )

    name = models.CharField(
        max_length=100
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    url_name = models.CharField(
        max_length=100
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    class Meta:

        db_table = "quick_links"

        ordering = [
            "category__display_order",
            "display_order",
            "name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "category",
                    "name",
                ],
                name="unique_quick_link_name_per_category"
            )
        ]

    def __str__(self):
        return self.name


# =========================================================
# NOTIFICATION
# =========================================================

def notification_image_upload_path(instance, filename):
    return get_instance_file_path(
        "notifications",
        instance,
        filename
    )


class Notification(
    FileReplaceMixin,
    BaseModel
):

    class NotificationType(models.TextChoices):

        GENERAL = "GENERAL", "General"

        SYSTEM = "SYSTEM", "System Update"

        FESTIVAL = "FESTIVAL", "Festival Update"

        FEATURE = "FEATURE", "New Feature"

        ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"

        PRODUCT = "PRODUCT", "Product Update"

        ORDER = "ORDER", "Order Update"

        PAYMENT = "PAYMENT", "Payment Update"

        WARNING = "WARNING", "Warning"

        SUCCESS = "SUCCESS", "Success"

    class Priority(models.TextChoices):

        LOW = "LOW", "Low"

        NORMAL = "NORMAL", "Normal"

        HIGH = "HIGH", "High"

        URGENT = "URGENT", "Urgent"

    notification_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        db_index=True
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_index=True
    )

    icon = models.CharField(
        max_length=100,
        default="ri-notification-3-line",
        blank=True
    )

    image = models.ImageField(
        upload_to=notification_image_upload_path,
        blank=True,
        null=True
    )

    # ---------------------------------------------------------
    # FILE MANAGEMENT
    # ---------------------------------------------------------

    file_fields = [
        "image",
    ]

    action_text = models.CharField(
        max_length=100,
        blank=True
    )

    action_url = models.CharField(
        max_length=500,
        blank=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    is_pinned = models.BooleanField(
        default=False,
        db_index=True
    )

    publish_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True
    )

    class Meta:

        db_table = "notifications"

        ordering = [
            "-is_pinned",
            "-publish_at",
            "-created_at",
        ]

    def __str__(self):
        return self.title

    @property
    def is_published(self):

        now = timezone.now()

        if not self.is_active:
            return False

        if self.publish_at > now:
            return False

        if self.expires_at and self.expires_at < now:
            return False

        return True


# =========================================================
# NOTIFICATION RECIPIENT
# =========================================================

class NotificationRecipient(BaseModel):

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients"
    )

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name="notification_recipients"
    )

    is_read = models.BooleanField(
        default=False,
        db_index=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:

        db_table = "notification_recipients"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "notification",
                    "user",
                ],
                name="unique_notification_user"
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "is_read",
                ]
            ),

            models.Index(
                fields=[
                    "notification",
                    "user",
                ]
            ),
        ]

    def mark_as_read(self):

        if not self.is_read:

            self.is_read = True

            self.read_at = timezone.now()

            self.save(
                update_fields=[
                    "is_read",
                    "read_at",
                    "updated_at",
                ]
            )