from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password

from .models import UserAccount, UserRole


# ============================================================
# USER ROLE ADMIN FORM
# ============================================================

class UserRoleAdminForm(forms.ModelForm):

    class Meta:
        model = UserRole
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if name:
            name = name.strip()

        return name

    def clean_code(self):
        code = self.cleaned_data.get("code")

        if code:
            code = code.strip().upper()

        return code


# ============================================================
# USER ROLE ADMIN
# ============================================================

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):

    # --------------------------------------------------------
    # LIST DISPLAY
    # --------------------------------------------------------

    list_display = (
        "name",
        "code",
        "user_count_display",
        "system_role_display",
        "status_display",
        "created_at",
        "updated_at",
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search_fields = (
        "id",
        "name",
        "code",
        "description",
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    list_filter = (
        "code",
        "is_system_role",
        "is_active",
        "created_at",
        "updated_at",
    )

    # --------------------------------------------------------
    # ORDERING
    # --------------------------------------------------------

    ordering = (
        "created_at",
    )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    list_per_page = 25

    # --------------------------------------------------------
    # READ ONLY
    # --------------------------------------------------------

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "user_count_display",
    )

    # --------------------------------------------------------
    # FIELDSETS
    # --------------------------------------------------------

    fieldsets = (

        (
            "Role Information",
            {
                "fields": (
                    "name",
                    "code",
                    "description",
                )
            }
        ),

        (
            "Role Settings",
            {
                "fields": (
                    "is_system_role",
                    "is_active",
                )
            }
        ),

        (
            "Role Statistics",
            {
                "fields": (
                    "user_count_display",
                )
            }
        ),

        (
            "System Information",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            }
        ),
    )

    # --------------------------------------------------------
    # READ ONLY SYSTEM ROLE CODE
    # --------------------------------------------------------

    def get_readonly_fields(self, request, obj=None):

        readonly_fields = [
            "id",
            "created_at",
            "updated_at",
            "user_count_display",
        ]

        if obj and obj.is_system_role:
            readonly_fields.append("code")

        return readonly_fields

    # --------------------------------------------------------
    # QUERYSET
    # --------------------------------------------------------

    def get_queryset(self, request):

        queryset = super().get_queryset(request)

        return queryset.annotate(
            total_users=Count("users")
        )

    # --------------------------------------------------------
    # USER COUNT
    # --------------------------------------------------------

    @admin.display(
        description="Users",
        ordering="total_users",
    )
    def user_count_display(self, obj):

        return obj.total_users

    # --------------------------------------------------------
    # SYSTEM ROLE BADGE
    # --------------------------------------------------------

    @admin.display(
        description="Type",
    )
    def system_role_display(self, obj):

        if obj.is_system_role:

            return format_html(
                '<span style="'
                'background:#153030;'
                'color:white;'
                'padding:4px 9px;'
                'border-radius:12px;'
                'font-size:11px;'
                'font-weight:600;'
                '">{}</span>',
                "SYSTEM",
            )

        return format_html(
            '<span style="'
            'background:#e5e7eb;'
            'color:#374151;'
            'padding:4px 9px;'
            'border-radius:12px;'
            'font-size:11px;'
            'font-weight:600;'
            '">{}</span>',
            "CUSTOM",
        )

    # --------------------------------------------------------
    # STATUS BADGE
    # --------------------------------------------------------

    @admin.display(
        description="Status",
    )
    def status_display(self, obj):

        if obj.is_active:

            return format_html(
                '<span style="'
                'color:#166534;'
                'font-weight:600;'
                '">{}</span>',
                "● Active",
            )

        return format_html(
            '<span style="'
            'color:#991b1b;'
            'font-weight:600;'
            '">{}</span>',
            "● Inactive",
        )

    # --------------------------------------------------------
    # DELETE PROTECTION
    # --------------------------------------------------------

    def has_delete_permission(self, request, obj=None):

        if obj and obj.is_system_role:
            return False

        return super().has_delete_permission(
            request,
            obj,
        )


# ============================================================
# USER ACCOUNT ADMIN FORM
# ============================================================

class UserAccountAdminForm(forms.ModelForm):

    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            render_value=False
        ),
        help_text=(
            "Leave blank when editing to keep the current "
            "password. Enter a password only when creating "
            "a user or changing the existing password."
        ),
    )

    class Meta:
        model = UserAccount
        fields = "__all__"

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

        return email

    # --------------------------------------------------------
    # FIRST NAME
    # --------------------------------------------------------

    def clean_first_name(self):

        first_name = self.cleaned_data.get("first_name")

        if first_name:
            first_name = first_name.strip()

        return first_name

    # --------------------------------------------------------
    # LAST NAME
    # --------------------------------------------------------

    def clean_last_name(self):

        last_name = self.cleaned_data.get("last_name")

        if last_name:
            last_name = last_name.strip()

        return last_name

    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

    def clean_phone(self):

        phone = self.cleaned_data.get("phone")

        if phone:
            phone = phone.strip()

        return phone

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    def save(self, commit=True):

        user = super().save(
            commit=False
        )

        password = self.cleaned_data.get(
            "password"
        )

        if password:

            user.set_password(
                password
            )

        if commit:
            user.save()

        return user


# ============================================================
# USER ACCOUNT ADMIN
# ============================================================

@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):

    form = UserAccountAdminForm

    # --------------------------------------------------------
    # LIST DISPLAY
    # --------------------------------------------------------

    list_display = (
        "profile_thumbnail",
        "full_name_display",
        "email",
        "phone",
        "role_display",
        "status_display",
        "last_login_display",
        "created_at_display",
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search_fields = (
        "id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "role__name",
        "role__code",
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    list_filter = (
        "role",
        "is_active",
        "role__is_system_role",
        "created_at",
        "updated_at",
        "last_login",
    )

    # --------------------------------------------------------
    # DATE HIERARCHY
    # --------------------------------------------------------

    date_hierarchy = "created_at"

    # --------------------------------------------------------
    # ORDERING
    # --------------------------------------------------------

    ordering = (
        "-created_at",
    )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    list_per_page = 25

    # --------------------------------------------------------
    # READ ONLY
    # --------------------------------------------------------

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "last_login",
        "profile_preview",
    )

    # --------------------------------------------------------
    # ROLE AUTOCOMPLETE
    # --------------------------------------------------------

    autocomplete_fields = (
        "role",
    )

    # --------------------------------------------------------
    # FIELDSETS
    # --------------------------------------------------------

    fieldsets = (

        # ====================================================
        # PERSONAL INFORMATION
        # ====================================================

        (
            "Personal Information",
            {
                "fields": (
                    "profile_preview",
                    "profile_image",
                    "first_name",
                    "last_name",
                )
            }
        ),

        # ====================================================
        # CONTACT INFORMATION
        # ====================================================

        (
            "Contact Information",
            {
                "fields": (
                    "email",
                    "phone",
                )
            }
        ),

        # ====================================================
        # ACCESS & SECURITY
        # ====================================================

        (
            "Access & Security",
            {
                "fields": (
                    "role",
                    "password",
                    "is_active",
                )
            }
        ),

        # ====================================================
        # LOGIN INFORMATION
        # ====================================================

        (
            "Login Information",
            {
                "fields": (
                    "last_login",
                )
            }
        ),

        # ====================================================
        # SYSTEM INFORMATION
        # ====================================================

        (
            "System Information",
            {
                "fields": (
                    "id",
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            }
        ),
    )

    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    actions = (
        "activate_users",
        "deactivate_users",
    )

    # ========================================================
    # PROFILE THUMBNAIL
    # ========================================================

    @admin.display(
        description="Profile",
    )
    def profile_thumbnail(self, obj):

        if obj.profile_image:

            return format_html(
                '<img src="{}" '
                'style="'
                'width:42px;'
                'height:42px;'
                'border-radius:50%;'
                'object-fit:cover;'
                'border:2px solid #e5e7eb;'
                '" />',
                obj.profile_image.url,
            )

        return "-"

    # ========================================================
    # FULL NAME
    # ========================================================

    @admin.display(
        description="Name",
        ordering="first_name",
    )
    def full_name_display(self, obj):

        return obj.full_name

    # ========================================================
    # ROLE
    # ========================================================

    @admin.display(
        description="Role",
        ordering="role__name",
    )
    def role_display(self, obj):

        if not obj.role:
            return "-"

        return format_html(
            "<strong>{}</strong>",
            obj.role.name,
        )

    # ========================================================
    # STATUS
    # ========================================================

    @admin.display(
        description="Status",
    )
    def status_display(self, obj):

        if obj.is_active:

            return format_html(
                '<span style="'
                'color:#166534;'
                'font-weight:600;'
                '">{}</span>',
                "● Active",
            )

        return format_html(
            '<span style="'
            'color:#991b1b;'
            'font-weight:600;'
            '">{}</span>',
            "● Inactive",
        )

    # ========================================================
    # LAST LOGIN
    # ========================================================

    @admin.display(
        description="Last Login",
        ordering="last_login",
    )
    def last_login_display(self, obj):

        if not obj.last_login:
            return "Never"

        return obj.last_login.strftime(
            "%d %b %Y, %I:%M %p"
        )

    # ========================================================
    # CREATED DATE
    # ========================================================

    @admin.display(
        description="Created",
        ordering="created_at",
    )
    def created_at_display(self, obj):

        return obj.created_at.strftime(
            "%d %b %Y, %I:%M %p"
        )

    # ========================================================
    # PROFILE PREVIEW
    # ========================================================

    @admin.display(
        description="Current Profile Image",
    )
    def profile_preview(self, obj):

        if not obj.profile_image:
            return "No profile image"

        return format_html(
            '<div>'
            '<img src="{}" '
            'style="'
            'width:140px;'
            'height:140px;'
            'border-radius:50%;'
            'object-fit:cover;'
            'border:3px solid #153030;'
            '" />'
            '</div>',
            obj.profile_image.url,
        )

    # ========================================================
    # ACTIVATE USERS
    # ========================================================

    @admin.action(
        description="Activate selected users"
    )
    def activate_users(
        self,
        request,
        queryset,
    ):

        updated = queryset.update(
            is_active=True
        )

        self.message_user(
            request,
            f"{updated} user(s) activated successfully.",
            messages.SUCCESS,
        )

    # ========================================================
    # DEACTIVATE USERS
    # ========================================================

    @admin.action(
        description="Deactivate selected users"
    )
    def deactivate_users(
        self,
        request,
        queryset,
    ):

        updated = queryset.update(
            is_active=False
        )

        self.message_user(
            request,
            f"{updated} user(s) deactivated successfully.",
            messages.WARNING,
        )