from django.urls import path
from apps.dashboard.views import *

urlpatterns = [
    path("", login_view, name="login_view"),
    path("logout/", logout_view, name="logout_view"),
    path("profile/", profile_view, name="profile_view"),
    path("quick-links/", quick_links, name="quick_links"),
    path("party/", party_list, name="party_list"),
    path("party/<uuid:pk>/", party_detail, name="party_detail"),
    path(
    "parties/<uuid:party_id>/orders/",party_orders_view,
    name="party_orders",
),

path(
    "purchase/<uuid:purchase_id>/",party_purchase_detail_view,
    name="party_purchase_detail",
),

path(
    "purchase/<uuid:purchase_id>/installments/",purchase_installments_view,
    name="purchase_installments",
),
path(
    "purchase/<uuid:purchase_id>/installments/",
    purchase_installments_view,
    name="purchase_installments",
),
    path("payments/", payment_list, name="payment_list"),
    path("dashboard/", dashboard_view, name="dashboard_view"),
    path(
        "notifications/",
        notification_list,
        name="notification_list"
    ),

    path(
        "notifications/<uuid:notification_id>/",
        notification_detail,
        name="notification_detail"
    ),

    path(
        "notifications/<uuid:notification_id>/read/",
        mark_notification_read,
        name="mark_notification_read"
    ),

    path(
        "notifications/<uuid:notification_id>/unread/",
        mark_notification_unread,
        name="mark_notification_unread"
    ),

    path(
        "notifications/read-all/",
        mark_all_notifications_read,
        name="mark_all_notifications_read"
    ),
    path(
        "pdf-overlay/",
        pdf_overlay_view,
        name="pdf_overlay"
    ),
]