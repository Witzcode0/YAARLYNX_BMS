from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from apps.accounts.models import UserAccount
from apps.dashboard.models import Party, PartyPaymentQR

from apps.dashboard.session import (
    get_logged_in_user,
    login_user,
    logout_user,
)

from apps.dashboard.decorators import (
    login_required,
    dashboard_access_required,
)


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

@dashboard_access_required
def payment_list(request):
    return render(
        request,
        "dashboard/payment_list.html",
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