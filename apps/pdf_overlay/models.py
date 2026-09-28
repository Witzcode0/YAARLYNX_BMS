from django.db import models
from apps.master.models import BaseModel

# Create your models here.
class OverlayImage(BaseModel):
    name = models.CharField(max_length=150)

    image = models.ImageField(
        upload_to="pdf_overlay/overlays/"
    )

    is_default = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Overlay Image"
        verbose_name_plural = "Overlay Images"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            OverlayImage.objects.exclude(
                pk=self.pk
            ).update(
                is_default=False
            )

        super().save(*args, **kwargs)