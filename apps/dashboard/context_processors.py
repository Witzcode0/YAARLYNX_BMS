from django.db.models import Q
from django.utils import timezone

from .models import NotificationRecipient


def notification_context(request):
    user_id = request.session.get("yaarlynx_user_id")

    if not user_id:
        return {
            "unread_notification_count": 0,
            "header_notifications": [],
        }

    now = timezone.now()

    header_notifications = (
        NotificationRecipient.objects
        .filter(
            user_id=user_id,
            notification__is_active=True,
            notification__publish_at__lte=now,
        )
        .filter(
            Q(notification__expires_at__isnull=True)
            | Q(notification__expires_at__gte=now)
        )
        .select_related("notification")
        .order_by(
            "-notification__is_pinned",
            "-notification__publish_at",
            "-created_at",
        )[:5]
    )

    unread_notification_count = (
        NotificationRecipient.objects
        .filter(
            user_id=user_id,
            is_read=False,
            notification__is_active=True,
            notification__publish_at__lte=now,
        )
        .filter(
            Q(notification__expires_at__isnull=True)
            | Q(notification__expires_at__gte=now)
        )
        .count()
    )

    return {
        "unread_notification_count": unread_notification_count,
        "header_notifications": header_notifications,
    }