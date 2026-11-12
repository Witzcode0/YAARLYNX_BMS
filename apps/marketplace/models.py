
from django.db import models
from apps.master.models import BaseModel


# ==========================================================
# MARKETPLACE MODEL
# ==========================================================

class Marketplace(BaseModel):

    name = models.CharField(
        max_length=150,
        unique=True
    )

    code = models.CharField(
        max_length=50,
        unique=True
    )

    website = models.URLField(
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = "marketplaces"
        ordering = ["name"]
        verbose_name = "Marketplace"
        verbose_name_plural = "Marketplaces"

    def __str__(self):
        return self.name


# ==========================================================
# COURIER PARTNER MODEL
# ==========================================================

class CourierPartner(BaseModel):

    name = models.CharField(
        max_length=150,
        unique=True
    )

    code = models.CharField(
        max_length=50,
        unique=True
    )

    # Contact Person Details
    contact_person_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    alternate_contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    # Address Details
    address = models.TextField(
        blank=True,
        null=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    # Website & Tracking Details
    website = models.URLField(
        blank=True,
        null=True
    )

    tracking_url = models.URLField(
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = "courier_partners"
        ordering = ["name"]
        verbose_name = "Courier Partner"
        verbose_name_plural = "Courier Partners"

    def __str__(self):
        return self.name


# ==========================================================
# MARKETPLACE COURIER PARTNER MAPPING MODEL
# ==========================================================

class MarketplaceCourierPartner(BaseModel):

    marketplace = models.ForeignKey(
        Marketplace,
        on_delete=models.PROTECT,
        related_name="courier_mappings"
    )

    courier_partner = models.ForeignKey(
        CourierPartner,
        on_delete=models.PROTECT,
        related_name="marketplace_mappings"
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        db_table = "marketplace_courier_partners"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "marketplace",
                    "courier_partner"
                ],
                name="unique_marketplace_courier_partner"
            )
        ]

        ordering = ["marketplace__name"]

        verbose_name = "Marketplace Courier Partner"
        verbose_name_plural = "Marketplace Courier Partners"

    def __str__(self):
        return (
            f"{self.marketplace.name} - "
            f"{self.courier_partner.name}"
        )
