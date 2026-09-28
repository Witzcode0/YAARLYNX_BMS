from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Prefetch
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone

from django.db.models import Sum, Count

from apps.accounts.models import UserAccount
from apps.dashboard.models import Party, PartyPaymentQR, PartyPurchase, PurchasePaymentInstallment, QuickLink, QuickLinkCategory, Notification, NotificationRecipient

from apps.dashboard.session import (
    get_logged_in_user,
    login_user,
    logout_user,
)

from apps.dashboard.decorators import (
    login_required,
    dashboard_access_required,
)

from django.shortcuts import render
from django.http import FileResponse

from apps.pdf_overlay.models import OverlayImage
from apps.pdf_overlay.services.pdf_processor import apply_overlay


# ==========================================================
# LOGIN
# ==========================================================
def login_view(request):

    # ------------------------------------------------------
    # STEP 1: CHECK ALREADY LOGGED-IN USER
    # ------------------------------------------------------

    current_user = get_logged_in_user(
        request
    )


    if current_user:

        # If already has dashboard access
        if current_user.has_dashboard_access:

            return redirect(
                "dashboard_view"
            )


    # ------------------------------------------------------
    # STEP 2: HANDLE POST
    # ------------------------------------------------------

    if request.method == "POST":

        # --------------------------------------------------
        # GET FORM DATA
        # --------------------------------------------------

        email = request.POST[
            "email"
        ].strip().lower()

        password = request.POST[
            "password"
        ]

        remember_me = request.POST.get(
            "remember_me"
        )


        # --------------------------------------------------
        # FIND USER
        # --------------------------------------------------

        try:

            user = (
                UserAccount.objects
                .select_related("role")
                .get(
                    email=email
                )
            )

        except UserAccount.DoesNotExist:

            return render(
                request,
                "dashboard/login.html",
                {
                    "error": (
                        "Invalid email or password."
                    ),
                    "email": email,
                }
            )


        # --------------------------------------------------
        # CHECK ACTIVE
        # --------------------------------------------------

        if not user.is_active:

            return render(
                request,
                "dashboard/login.html",
                {
                    "error": (
                        "Your account has been deactivated."
                    ),
                    "email": email,
                }
            )


        # --------------------------------------------------
        # CHECK PASSWORD
        # --------------------------------------------------

        if not user.check_password(
            password
        ):

            return render(
                request,
                "dashboard/login.html",
                {
                    "error": (
                        "Invalid email or password."
                    ),
                    "email": email,
                }
            )


        # --------------------------------------------------
        # CHECK DASHBOARD ACCESS
        # --------------------------------------------------

        if not user.has_dashboard_access:

            return render(
                request,
                "dashboard/login.html",
                {
                    "error": (
                        "You do not have permission "
                        "to access the dashboard."
                    ),
                    "email": email,
                }
            )


        # --------------------------------------------------
        # LOGIN
        # --------------------------------------------------

        login_user(
            request,
            user
        )


        # --------------------------------------------------
        # REMEMBER ME
        # --------------------------------------------------

        if remember_me:

            # 30 days
            request.session.set_expiry(
                60 * 60 * 24 * 30
            )

        else:

            # Browser session
            request.session.set_expiry(
                0
            )

        # --------------------------------------------------
        # REDIRECT DASHBOARD
        # --------------------------------------------------

        return redirect(
            "dashboard_view"
        )


    # ------------------------------------------------------
    # GET LOGIN PAGE
    # ------------------------------------------------------

    return render(
        request,
        "dashboard/login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================
@login_required
def logout_view(request):

    # ------------------------------------------------------
    # DESTROY CUSTOM SESSION
    # ------------------------------------------------------

    logout_user(
        request
    )


    # ------------------------------------------------------
    # SUCCESS MESSAGE
    # ------------------------------------------------------

    messages.success(
        request,
        "You have been logged out successfully."
    )


    # ------------------------------------------------------
    # REDIRECT LOGIN
    # ------------------------------------------------------

    return redirect(
        "login_view"
    )


# ==========================================================
# DASHBOARD
# ==========================================================
@dashboard_access_required
def dashboard_view(request):

    # =====================================================
    # CURRENT USER
    # =====================================================

    user = request.current_user

    # =====================================================
    # PARTY STATISTICS
    # =====================================================

    total_parties = Party.objects.count()

    active_parties = Party.objects.filter(
        is_active=True
    ).count()

    inactive_parties = Party.objects.filter(
        is_active=False
    ).count()

    gst_parties = (
        Party.objects
        .exclude(gst_number="")
        .exclude(gst_number__isnull=True)
        .count()
    )

    bank_parties = (
        Party.objects
        .exclude(bank_name="")
        .exclude(bank_name__isnull=True)
        .exclude(account_number="")
        .exclude(account_number__isnull=True)
        .count()
    )

    total_qrs = PartyPaymentQR.objects.count()

    active_qrs = PartyPaymentQR.objects.filter(
        is_active=True
    ).count()

    # =====================================================
    # PARTY TYPES
    # =====================================================

    party_type_data = []

    for value, label in Party.PartyType.choices:

        count = Party.objects.filter(
            party_type=value
        ).count()

        party_type_data.append(
            {
                "value": value,
                "label": label,
                "count": count,
            }
        )

    # =====================================================
    # RECENT PARTIES
    # =====================================================

    recent_parties = (
        Party.objects
        .order_by("-created_at")[:8]
    )

    # =====================================================
    # RECENTLY UPDATED PARTIES
    # =====================================================

    recently_updated_parties = (
        Party.objects
        .order_by("-updated_at")[:5]
    )

    # =====================================================
    # PARTIES NEEDING ATTENTION
    # =====================================================

    parties_without_gst = (
        Party.objects
        .filter(is_active=True)
        .filter(
            gst_number=""
        )
        .order_by("name")[:5]
    )

    parties_without_bank = (
        Party.objects
        .filter(is_active=True)
        .filter(
            bank_name=""
        )
        .order_by("name")[:5]
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {
        "user": user,

        # Statistics
        "total_parties": total_parties,
        "active_parties": active_parties,
        "inactive_parties": inactive_parties,
        "gst_parties": gst_parties,
        "bank_parties": bank_parties,
        "total_qrs": total_qrs,
        "active_qrs": active_qrs,

        # Party types
        "party_type_data": party_type_data,

        # Lists
        "recent_parties": recent_parties,
        "recently_updated_parties": recently_updated_parties,

        # Attention
        "parties_without_gst": parties_without_gst,
        "parties_without_bank": parties_without_bank,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )



@dashboard_access_required
def party_list(request):
    """
    Party listing with real-time search/filter support.

    Supports:
    - Search
    - Party type
    - Status
    - Pagination
    """

    search = request.GET.get("search", "").strip()
    party_type = request.GET.get("party_type", "").strip()
    status = request.GET.get("status", "").strip()

    parties = (
        Party.objects
        .prefetch_related("payment_qrs")
        .all()
    )

    # -----------------------------------
    # SEARCH
    # -----------------------------------
    if search:
        parties = parties.filter(
            Q(name__icontains=search)
            | Q(contact_person__icontains=search)
            | Q(phone__icontains=search)
            | Q(alternate_phone__icontains=search)
            | Q(email__icontains=search)
            | Q(gst_number__icontains=search)
            | Q(city__icontains=search)
            | Q(state__icontains=search)
            | Q(pincode__icontains=search)
            | Q(bank_name__icontains=search)
            | Q(account_holder_name__icontains=search)
            | Q(account_number__icontains=search)
            | Q(ifsc_code__icontains=search)
            | Q(branch_name__icontains=search)
            | Q(upi_id__icontains=search)
            | Q(gpay_number__icontains=search)
        )

    # -----------------------------------
    # PARTY TYPE FILTER
    # -----------------------------------
    if party_type:
        parties = parties.filter(
            party_type=party_type
        )

    # -----------------------------------
    # STATUS FILTER
    # -----------------------------------
    if status == "active":
        parties = parties.filter(is_active=True)

    elif status == "inactive":
        parties = parties.filter(is_active=False)

    # -----------------------------------
    # PAGINATION
    # -----------------------------------
    paginator = Paginator(parties, 15)

    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "parties": page_obj.object_list,

        "search": search,
        "party_type": party_type,
        "status": status,

        "party_types": Party.PartyType.choices,

        "total_parties": Party.objects.count(),
        "active_parties": Party.objects.filter(
            is_active=True
        ).count(),
        "inactive_parties": Party.objects.filter(
            is_active=False
        ).count(),
    }

    # -----------------------------------
    # AJAX / HTMX-LIKE PARTIAL REQUEST
    # -----------------------------------
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "dashboard/party_table.html",
            context
        )

    return render(
        request,
        "dashboard/party_list.html",
        context
    )


@dashboard_access_required
def party_detail(request, pk):
    party = get_object_or_404(
        Party.objects.prefetch_related("payment_qrs"),
        pk=pk
    )

    return render(
        request,
        "dashboard/party_detail.html",
        {
            "party": party,
        }
    )


def party_orders_view(request, party_id):
    """
    Display all purchase orders for a particular party.
    """

    party = get_object_or_404(
        Party,
        pk=party_id,
    )


    orders = (
        PartyPurchase.objects
        .filter(party=party)
        .select_related("party")
        .order_by(
            "-purchase_date",
            "-created_at",
        )
    )

    summary = orders.aggregate(
        total_purchase=Sum("grand_total"),
        total_paid=Sum("paid_amount"),
        total_due=Sum("due_amount"),
    )

    total_purchase = (
        summary["total_purchase"]
        or Decimal("0.00")
    )

    total_paid = (
        summary["total_paid"]
        or Decimal("0.00")
    )

    total_due = (
        summary["total_due"]
        or Decimal("0.00")
    )

    context = {
        "party": party,
        "orders": orders,

        "total_orders": orders.count(),

        "total_purchase": total_purchase,

        "total_paid": total_paid,

        "total_due": total_due,
    }

    return render(
        request,
        "dashboard/party_orders.html",
        context,
    )

def party_purchase_detail_view(request, purchase_id):

    purchase = get_object_or_404(
        PartyPurchase.objects.select_related("party"),
        pk=purchase_id,
    )

    installments = (
        PurchasePaymentInstallment.objects
        .filter(purchase=purchase)
        .select_related("payment_method")
        .order_by("installment_number")
    )

    installment_summary = installments.aggregate(
        total_installment=Sum("installment_amount"),
        total_paid=Sum("paid_amount"),
        total_remaining=Sum("remaining_amount"),
    )

    context = {
        "purchase": purchase,
        "party": purchase.party,
        "installments": installments,

        "total_installments": installments.count(),

        "total_installment": (
            installment_summary["total_installment"]
            or Decimal("0.00")
        ),

        "installment_paid": (
            installment_summary["total_paid"]
            or Decimal("0.00")
        ),

        "installment_remaining": (
            installment_summary["total_remaining"]
            or Decimal("0.00")
        ),
    }

    return render(
        request,
        "dashboard/party_purchase_detail.html",
        context,
    )
def purchase_installments_view(request, purchase_id):

    purchase = get_object_or_404(
        PartyPurchase.objects.select_related("party"),
        pk=purchase_id,
    )

    installments = (
        PurchasePaymentInstallment.objects
        .filter(purchase=purchase)
        .select_related("payment_method")
        .order_by("installment_number")
    )

    summary = installments.aggregate(
        total_installment=Sum("installment_amount"),
        total_paid=Sum("paid_amount"),
        total_remaining=Sum("remaining_amount"),
    )

    context = {
        "purchase": purchase,
        "party": purchase.party,
        "installments": installments,

        "total_installments": installments.count(),

        "total_installment": (
            summary["total_installment"]
            or Decimal("0.00")
        ),

        "total_paid": (
            summary["total_paid"]
            or Decimal("0.00")
        ),

        "total_remaining": (
            summary["total_remaining"]
            or Decimal("0.00")
        ),
    }

    return render(
        request,
        "dashboard/purchase_installments.html",
        context,
    )

@dashboard_access_required
def payment_list(request):
    installments = (
        PurchasePaymentInstallment.objects
        .select_related(
            "purchase",
            "purchase__party",
            "payment_method",
        )
        .order_by("-payment_date", "-created_at")
    )

    purchase_summary = PartyPurchase.objects.aggregate(
        total_purchase=Sum("grand_total"),
        total_paid=Sum("paid_amount"),
        total_due=Sum("due_amount"),
    )

    payment_summary = installments.aggregate(
        total_payment_records=Count("id"),
        total_installment_amount=Sum("installment_amount"),
        total_paid_amount=Sum("paid_amount"),
        total_remaining_amount=Sum("remaining_amount"),
    )

    recent_payments = (
        installments
        .filter(paid_amount__gt=Decimal("0.00"))
        .order_by("-payment_date", "-created_at")[:10]
    )

    payment_methods = (
        installments
        .filter(paid_amount__gt=Decimal("0.00"))
        .values(
            "payment_method__name"
        )
        .annotate(
            total_amount=Sum("paid_amount"),
            payment_count=Count("id"),
        )
        .order_by("-total_amount")
    )

    total_paid = (
        payment_summary["total_paid_amount"]
        or Decimal("0.00")
    )

    total_purchase = (
        purchase_summary["total_purchase"]
        or Decimal("0.00")
    )

    payment_percentage = Decimal("0.00")

    if total_purchase > Decimal("0.00"):
        payment_percentage = (
            total_paid / total_purchase
        ) * Decimal("100.00")

    context = {
        "total_payments": (
            payment_summary["total_payment_records"] or 0
        ),

        "total_installment_amount": (
            payment_summary["total_installment_amount"]
            or Decimal("0.00")
        ),

        "total_paid": (
            payment_summary["total_paid_amount"]
            or Decimal("0.00")
        ),

        "total_remaining": (
            payment_summary["total_remaining_amount"]
            or Decimal("0.00")
        ),

        "total_purchase": total_purchase,

        "purchase_paid": (
            purchase_summary["total_paid"]
            or Decimal("0.00")
        ),

        "purchase_due": (
            purchase_summary["total_due"]
            or Decimal("0.00")
        ),

        "payment_percentage": min(
            payment_percentage,
            Decimal("100.00")
        ),

        "recent_payments": recent_payments,

        "payment_methods": payment_methods,
    }

    return render(
        request,
        "dashboard/payment_list.html",
        context,
    )

# ==========================================================
# USER PROFILE
# ==========================================================
@login_required
def profile_view(request):

    # ------------------------------------------------------
    # GET CURRENT LOGGED-IN USER
    # ------------------------------------------------------

    user = request.current_user


    # ------------------------------------------------------
    # RENDER PROFILE PAGE
    # ------------------------------------------------------

    return render(
        request,
        "dashboard/profile.html",
        {
            "user": user,
        }
    )

def quick_links(request):

    active_quick_links = (
        QuickLink.objects
        .filter(is_active=True)
        .order_by("display_order", "name")
    )

    categories = (
        QuickLinkCategory.objects
        .filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "quick_links",
                queryset=active_quick_links,
                to_attr="active_quick_links"
            )
        )
        .order_by("display_order", "name")
    )

    # Remove categories that have no active quick links
    categories = [
        category
        for category in categories
        if category.active_quick_links
    ]

    return render(
        request,
        "dashboard/quick_links.html",
        {
            "categories": categories,
        }
    )

def notification_list(request):
    """
    Display notifications available for the logged-in user.
    """

    user_id = request.session.get("yaarlynx_user_id")

    if not user_id:
        return redirect("login")

    user = get_object_or_404(
        UserAccount,
        id=user_id
    )

    recipients = (
        NotificationRecipient.objects
        .filter(
            user=user,
            notification__is_active=True,
            notification__publish_at__lte=timezone.now(),
        )
        .select_related("notification")
        .order_by(
            "-notification__is_pinned",
            "-notification__publish_at",
            "-created_at",
        )
    )

    # Remove expired notifications
    recipients = [
        recipient
        for recipient in recipients
        if recipient.notification.is_published
    ]

    total_notifications = len(recipients)

    unread_count = sum(
        1
        for recipient in recipients
        if not recipient.is_read
    )

    context = {
        "recipients": recipients,
        "total_notifications": total_notifications,
        "unread_count": unread_count,
    }

    return render(
        request,
        "dashboard/notifications.html",
        context
    )

def notification_detail(request, notification_id):
    """
    Display notification details and mark notification as read.
    """

    user_id = request.session.get("yaarlynx_user_id")

    if not user_id:
        return redirect("login")

    user = get_object_or_404(
        UserAccount,
        id=user_id
    )

    recipient = get_object_or_404(
        NotificationRecipient.objects.select_related(
            "notification"
        ),
        notification__notification_id=notification_id,
        user=user,
        notification__is_active=True,
    )

    notification = recipient.notification

    # Check publication status
    if not notification.is_published:

        return redirect("notification_list")

    # Mark as read
    recipient.mark_as_read()

    context = {
        "notification": notification,
        "recipient": recipient,
    }

    return render(
        request,
        "dashboard/notification_detail.html",
        context
    )

def mark_notification_read(request, notification_id):
    """
    Mark a notification as read.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method."
            },
            status=400
        )

    user_id = request.session.get(
        "yaarlynx_user_id"
    )

    if not user_id:

        return JsonResponse(
            {
                "success": False,
                "message": "Authentication required."
            },
            status=401
        )

    recipient = get_object_or_404(
        NotificationRecipient,
        notification__notification_id=notification_id,
        user_id=user_id,
    )

    recipient.mark_as_read()

    return JsonResponse(
        {
            "success": True,
            "message": "Notification marked as read."
        }
    )

def mark_all_notifications_read(request):
    """
    Mark all notifications of the logged-in user as read.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method."
            },
            status=400
        )

    user_id = request.session.get(
        "yaarlynx_user_id"
    )

    if not user_id:

        return JsonResponse(
            {
                "success": False,
                "message": "Authentication required."
            },
            status=401
        )

    recipients = NotificationRecipient.objects.filter(
        user_id=user_id,
        is_read=False,
        notification__is_active=True,
    )

    updated_count = recipients.update(
        is_read=True,
        read_at=timezone.now(),
    )

    return JsonResponse(
        {
            "success": True,
            "message": "All notifications marked as read.",
            "updated_count": updated_count,
        }
    )

def mark_notification_unread(request, notification_id):
    """
    Mark a notification as unread.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method."
            },
            status=400
        )

    user_id = request.session.get(
        "yaarlynx_user_id"
    )

    if not user_id:

        return JsonResponse(
            {
                "success": False,
                "message": "Authentication required."
            },
            status=401
        )

    recipient = get_object_or_404(
        NotificationRecipient,
        notification__notification_id=notification_id,
        user_id=user_id,
    )

    recipient.mark_as_unread()

    return JsonResponse(
        {
            "success": True,
            "message": "Notification marked as unread."
        }
    )




def pdf_overlay_view(request):

    # ========================================================
    # GET ALL OVERLAY IMAGES
    # ========================================================

    overlay_images = OverlayImage.objects.all()


    # ========================================================
    # GET DEFAULT OVERLAY
    # ========================================================

    default_overlay = OverlayImage.objects.filter(
        is_default=True
    ).first()


    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        # ----------------------------------------------------
        # GET UPLOADED PDF
        # ----------------------------------------------------

        pdf_file = request.FILES.get(
            "pdf_file"
        )


        # ----------------------------------------------------
        # Validate PDF
        # ----------------------------------------------------

        if not pdf_file:

            return render(
                request,
                "dashboard/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Please upload a PDF file.",
                }
            )


        # ----------------------------------------------------
        # Check extension
        # ----------------------------------------------------

        if not pdf_file.name.lower().endswith(
            ".pdf"
        ):

            return render(
                request,
                "dashboard/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Only PDF files are allowed.",
                }
            )


        # ====================================================
        # GET SELECTED OVERLAY
        # ====================================================

        overlay_id = request.POST.get(
            "overlay_image"
        )


        if not overlay_id:

            return render(
                request,
                "dashboard/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Please select an overlay image.",
                }
            )


        # ====================================================
        # GET OVERLAY OBJECT
        # ====================================================

        try:

            overlay = OverlayImage.objects.get(
                pk=overlay_id
            )

        except OverlayImage.DoesNotExist:

            return render(
                request,
                "dashboard/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": "Selected overlay image was not found.",
                }
            )


        # ====================================================
        # GET POSITION
        # ====================================================

        position = request.POST.get(
            "position",
            "bottom_center"
        )


        # ====================================================
        # ALLOWED POSITIONS
        # ====================================================

        allowed_positions = {
            "bottom_left",
            "bottom_center",
            "bottom_right",
            "top_left",
            "top_center",
            "top_right",
            "center",
        }


        if position not in allowed_positions:

            position = "bottom_center"


        # ====================================================
        # PROCESS PDF
        # ====================================================

        try:

            result = apply_overlay(
                pdf_file=pdf_file,
                image_path=overlay.image.path,
                position=position,
            )

        except Exception as error:

            return render(
                request,
                "dashboard/overlay.html",
                {
                    "overlay_images": overlay_images,
                    "default_overlay": default_overlay,
                    "error": (
                        f"Unable to process PDF: {error}"
                    ),
                }
            )


        # ====================================================
        # DOWNLOAD
        # ====================================================

        return FileResponse(
            result,
            as_attachment=True,
            filename="pdf_overlay_result.pdf",
            content_type="application/pdf",
        )


    # ========================================================
    # GET REQUEST
    # ========================================================

    return render(
        request,
    "dashboard/overlay.html",
        {
            "overlay_images": overlay_images,
            "default_overlay": default_overlay,
        }
    )