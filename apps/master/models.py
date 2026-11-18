from django.db import models
import uuid


class BaseModel(models.Model):
    """
    Common abstract base model for all Yaarlynx models.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    class Meta:
        abstract = True

class MeasurementUnit(BaseModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    short_name = models.CharField(
        max_length=20,
        unique=True,
        help_text="Example: PCS, KG, GM, BOX"
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        db_table = "measurement_units"
        ordering = ["name"]
        verbose_name = "Measurement Unit"
        verbose_name_plural = "Measurement Units"

    def __str__(self):
        return f"{self.name} ({self.short_name})"