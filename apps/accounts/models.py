from django.db import models

from apps.master.models import BaseModel

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

import os

class UserRole(BaseModel):

    class RoleCode(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        CUSTOMER = "CUSTOMER", "Customer"

    name = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=30,
        choices=RoleCode.choices,
        unique=True,
        db_index=True
    )

    description = models.TextField(
        blank=True
    )

    is_system_role = models.BooleanField(
        default=False,
        db_index=True
    )

    class Meta:
        db_table = "user_roles"
        ordering = ["created_at"]
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    def __str__(self):
        return self.name



def user_profile_upload_path(instance, filename):
    """
    Store profile image as:

    users/profile/<instance.id>.<extension>

    Example:

    users/profile/
        1f7b2c89-1234-4567-8901-abcdef123456.jpg
    """

    extension = os.path.splitext(filename)[1].lower()

    return f"users/profile/{instance.id}{extension}"



class UserAccount(BaseModel):

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    email = models.EmailField(
        unique=True,
        db_index=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    password = models.CharField(
        max_length=255
    )

    role = models.ForeignKey(
        UserRole,
        on_delete=models.PROTECT,
        related_name="users",
        db_index=True
    )

    last_login = models.DateTimeField(
        null=True,
        blank=True
    )

    profile_image = models.ImageField(
        upload_to=user_profile_upload_path,
        default="default/profile.png",
        blank=True
    )

    class Meta:
        db_table = "user_accounts"
        ordering = ["-created_at"]
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"

    def __str__(self):
        return self.email

    # --------------------------------------------------
    # NAME
    # --------------------------------------------------

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    # --------------------------------------------------
    # ROLE CHECKS
    # --------------------------------------------------

    @property
    def is_super_admin(self):
        return self.role.code == UserRole.RoleCode.SUPER_ADMIN

    @property
    def is_admin(self):
        return self.role.code in [
            UserRole.RoleCode.SUPER_ADMIN,
            UserRole.RoleCode.ADMIN,
        ]

    @property
    def is_staff_user(self):
        return self.role.code == UserRole.RoleCode.STAFF

    @property
    def is_customer(self):
        return self.role.code == UserRole.RoleCode.CUSTOMER

    @property
    def has_dashboard_access(self):
        return self.role.code in [
            UserRole.RoleCode.SUPER_ADMIN,
            UserRole.RoleCode.ADMIN,
            UserRole.RoleCode.STAFF,
        ]

    # --------------------------------------------------
    # PASSWORD
    # --------------------------------------------------

    def set_password(self, raw_password):
        """
        Hash and store password securely.
        """

        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Check raw password against stored hash.
        """

        return check_password(
            raw_password,
            self.password
        )

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    def save(self, *args, **kwargs):

        old_profile_image = None

        # Normalize email
        if self.email:
            self.email = self.email.strip().lower()

        # Check old profile image before updating
        if self.pk:

            try:
                old_user = UserAccount.objects.get(
                    pk=self.pk
                )

                old_profile_image = old_user.profile_image

            except UserAccount.DoesNotExist:
                pass

        # Save new data
        super().save(*args, **kwargs)

        # Delete old profile image if replaced
        if (
            old_profile_image
            and old_profile_image.name
            and old_profile_image.name != self.profile_image.name
            and old_profile_image.name != "default/profile.png"
        ):

            if old_profile_image.storage.exists(
                old_profile_image.name
            ):
                old_profile_image.storage.delete(
                    old_profile_image.name
                )

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def delete(self, *args, **kwargs):

        profile_image = self.profile_image

        super().delete(*args, **kwargs)

        # Delete user's uploaded profile image
        if (
            profile_image
            and profile_image.name
            and profile_image.name != "default/profile.png"
        ):

            if profile_image.storage.exists(
                profile_image.name
            ):
                profile_image.storage.delete(
                    profile_image.name
                )