from django.db import models

from django.contrib.auth.hashers import (
    check_password,
    make_password,
)

from apps.master.models import BaseModel
from apps.master.utils import get_instance_file_path
from apps.master.mixins import FileReplaceMixin


# ============================================================
# USER ROLE
# ============================================================

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


# ============================================================
# PROFILE IMAGE UPLOAD PATH
# ============================================================

def user_profile_upload_path(instance, filename):

    return get_instance_file_path(
        "users/profile",
        instance,
        filename
    )


# ============================================================
# USER ACCOUNT
# ============================================================

class UserAccount(
    FileReplaceMixin,
    BaseModel
):

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

    # ========================================================
    # FILE FIELDS MANAGED BY FileReplaceMixin
    # ========================================================

    file_fields = [
        "profile_image",
    ]

    class Meta:
        db_table = "user_accounts"
        ordering = ["-created_at"]
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"

    def __str__(self):
        return self.email

    # ========================================================
    # NAME
    # ========================================================

    @property
    def full_name(self):

        return f"{self.first_name} {self.last_name}".strip()

    # ========================================================
    # ROLE CHECKS
    # ========================================================

    @property
    def is_super_admin(self):

        return (
            self.role.code
            == UserRole.RoleCode.SUPER_ADMIN
        )

    @property
    def is_admin(self):

        return self.role.code in [
            UserRole.RoleCode.SUPER_ADMIN,
            UserRole.RoleCode.ADMIN,
        ]

    @property
    def is_staff_user(self):

        return (
            self.role.code
            == UserRole.RoleCode.STAFF
        )

    @property
    def is_customer(self):

        return (
            self.role.code
            == UserRole.RoleCode.CUSTOMER
        )

    @property
    def has_dashboard_access(self):

        return self.role.code in [
            UserRole.RoleCode.SUPER_ADMIN,
            UserRole.RoleCode.ADMIN,
            UserRole.RoleCode.STAFF,
        ]

    # ========================================================
    # PASSWORD
    # ========================================================

    def set_password(self, raw_password):

        self.password = make_password(
            raw_password
        )

    def check_password(self, raw_password):

        return check_password(
            raw_password,
            self.password
        )

    # ========================================================
    # SAVE
    # ========================================================

    def save(self, *args, **kwargs):

        # Normalize email
        if self.email:

            self.email = (
                self.email
                .strip()
                .lower()
            )

        # FileReplaceMixin handles:
        # - old file detection
        # - new file save
        # - old file deletion

        super().save(
            *args,
            **kwargs
        )