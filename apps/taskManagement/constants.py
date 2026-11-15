class TaskPriority:

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    CHOICES = [
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (URGENT, "Urgent"),
    ]


class TaskStatus:

    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (IN_PROGRESS, "In Progress"),
        (ON_HOLD, "On Hold"),
        (UNDER_REVIEW, "Under Review"),
        (COMPLETED, "Completed"),
        (REJECTED, "Rejected"),
        (CANCELLED, "Cancelled"),
    ]


class TaskRecurrence:

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

    CHOICES = [
        (NONE, "No Recurrence"),
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
    ]