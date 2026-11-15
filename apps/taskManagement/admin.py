from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Q

from .models import (
    TaskCategory,
    Task,
    TaskAssignment,
    TaskComment,
    TaskActivity,
    TaskChecklist,
    TaskAttachment,
)


# ============================================================
# COMMON ADMIN HELPERS
# ============================================================

class TaskAdminBase(admin.ModelAdmin):
    """Shared admin behaviour for task-management records."""

    date_hierarchy = "created_at"
    save_on_top = True
    empty_value_display = "—"


# ============================================================
# INLINE ADMIN CLASSES
# ============================================================

class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    extra = 0
    show_change_link = True
    fields = (
        "user",
        "assigned_by",
        "status",
        "progress",
        "assigned_at",
        "accepted_at",
        "started_at",
        "submitted_at",
        "completed_at",
    )
    readonly_fields = (
        "assigned_at",
        "accepted_at",
        "started_at",
        "submitted_at",
        "completed_at",
    )
    raw_id_fields = ("user", "assigned_by")
    ordering = ("-assigned_at",)


class TaskChecklistInline(admin.TabularInline):
    model = TaskChecklist
    extra = 0
    show_change_link = True
    fields = ("title", "is_completed", "completed_by", "completed_at")
    readonly_fields = ("completed_at",)
    raw_id_fields = ("completed_by",)


class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    show_change_link = True
    fields = (
        "document_number",
        "sequence",
        "title",
        "original_filename",
        "file",
        "version",
        "uploaded_by",
        "replaced_at",
    )
    readonly_fields = (
        "document_number",
        "sequence",
        "original_filename",
        "version",
        "replaced_at",
    )
    raw_id_fields = ("uploaded_by",)


class TaskActivityInline(admin.TabularInline):
    model = TaskActivity
    extra = 0
    can_delete = False
    max_num = 0
    fields = ("created_at", "user", "action", "description", "old_value", "new_value")
    readonly_fields = fields
    raw_id_fields = ("user",)


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    show_change_link = True
    fields = ("created_at", "user", "comment", "parent", "assignment")
    readonly_fields = ("created_at",)
    raw_id_fields = ("user", "assignment", "parent")


# ============================================================
# TASK CATEGORY ADMIN
# ============================================================

@admin.register(TaskCategory)
class TaskCategoryAdmin(TaskAdminBase):
    list_display = ("name", "color_preview", "description", "category_task_count", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Category Information", {
            "fields": ("name", "description", "color"),
            "description": "Create a category to group tasks by department or workflow.",
        }),
        ("System Information", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Color")
    def color_preview(self, obj):
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:7px;">'
            '<span style="width:18px;height:18px;border-radius:5px;'
            'background:{};border:1px solid #aaa;display:inline-block;"></span>{}'
            '</span>',
            obj.color,
            obj.color,
        )

    @admin.display(description="Tasks", ordering="admin_task_count")
    def category_task_count(self, obj):
        return getattr(obj, "admin_task_count", obj.tasks.count())

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            admin_task_count=Count("tasks", distinct=True)
        )


# ============================================================
# MAIN TASK ADMIN
# ============================================================

@admin.register(Task)
class TaskAdmin(TaskAdminBase):
    list_display = (
        "task_number",
        "title",
        "category",
        "priority_badge",
        "task_status_summary",
        "assigned_count",
        "progress_summary",
        "due_date",
        "overdue_badge",
        "approval_badge",
        "created_by",
        "created_at",
    )
    list_display_links = ("task_number", "title")
    list_filter = (
        "priority",
        "recurrence",
        "is_approved",
        "category",
        "due_date",
        "created_at",
    )
    search_fields = (
        "task_number",
        "title",
        "description",
        "created_by__first_name",
        "created_by__last_name",
        "created_by__email",
        "assignments__user__first_name",
        "assignments__user__last_name",
        "assignments__user__email",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "task_number",
        "created_at",
        "updated_at",
        "assigned_count_readonly",
        "completed_count_readonly",
        "average_progress_readonly",
        "document_count_readonly",
        "checklist_summary_readonly",
        "overdue_readonly",
    )
    raw_id_fields = ("created_by", "approved_by")
    inlines = (
        TaskAssignmentInline,
        TaskChecklistInline,
        TaskAttachmentInline,
        TaskCommentInline,
        TaskActivityInline,
    )
    list_select_related = ("category", "created_by", "approved_by")
    list_per_page = 30
    fieldsets = (
        ("Task Identification", {
            "fields": ("task_number", "title", "description", "category"),
        }),
        ("Planning & Priority", {
            "fields": ("priority", "recurrence", "start_date", "due_date"),
        }),
        ("Ownership", {
            "fields": ("created_by",),
        }),
        ("Approval", {
            "fields": ("is_approved", "approved_by", "approved_at"),
        }),
        ("Task Insights", {
            "fields": (
                "assigned_count_readonly",
                "completed_count_readonly",
                "average_progress_readonly",
                "document_count_readonly",
                "checklist_summary_readonly",
                "overdue_readonly",
            ),
            "classes": ("collapse",),
        }),
        ("System Information", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("category", "created_by", "approved_by")
            .annotate(
                admin_assignment_count=Count("assignments", distinct=True),
                admin_completed_count=Count(
                    "assignments",
                    filter=Q(assignments__status="completed"),
                    distinct=True,
                ),
                admin_average_progress=Avg("assignments__progress"),
            )
        )

    @admin.display(description="Priority")
    def priority_badge(self, obj):
        colors = {
            "low": "#64748b",
            "medium": "#2563eb",
            "high": "#d97706",
            "urgent": "#dc2626",
        }
        color = colors.get(obj.priority, "#475569")
        return format_html(
            '<span style="background:{}18;color:{};padding:4px 9px;'
            'border-radius:20px;font-weight:700;">{}</span>',
            color, color, obj.get_priority_display(),
        )

    @admin.display(description="Assignments")
    def task_status_summary(self, obj):
        total = getattr(obj, "admin_assignment_count", 0)
        completed = getattr(obj, "admin_completed_count", 0)
        if not total:
            return "Not assigned"
        return f"{completed}/{total} completed"

    @admin.display(description="Assigned")
    def assigned_count(self, obj):
        return getattr(obj, "admin_assignment_count", 0)

    @admin.display(description="Progress")
    def progress_summary(self, obj):
        value = round(obj.admin_average_progress or 0)
        return format_html(
            '<div style="min-width:90px;">'
            '<div style="font-weight:700;margin-bottom:3px;">{}%</div>'
            '<div style="height:6px;background:#e5e7eb;border-radius:8px;">'
            '<div style="height:6px;width:{}%;background:#153030;'
            'border-radius:8px;"></div></div></div>',
            value, value,
        )

    @admin.display(description="Due Status")
    def overdue_badge(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span style="color:#dc2626;font-weight:700;">Overdue</span>'
            )
        if obj.due_date:
            return "On schedule" if obj.due_date >= __import__("django").utils.timezone.localdate() else "Closed / past due"
        return "No due date"

    @admin.display(description="Approval")
    def approval_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="color:#15803d;font-weight:700;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color:#b45309;font-weight:700;">Pending</span>'
        )

    @admin.display(description="Assigned users")
    def assigned_count_readonly(self, obj):
        return obj.assigned_user_count

    @admin.display(description="Completed assignments")
    def completed_count_readonly(self, obj):
        return obj.completed_user_count

    @admin.display(description="Average progress")
    def average_progress_readonly(self, obj):
        return f"{obj.average_progress}%"

    @admin.display(description="Documents")
    def document_count_readonly(self, obj):
        return obj.document_count

    @admin.display(description="Checklist")
    def checklist_summary_readonly(self, obj):
        return f"{obj.completed_checklist_count} / {obj.checklist_count} completed"

    @admin.display(description="Overdue")
    def overdue_readonly(self, obj):
        return "Yes" if obj.is_overdue else "No"


# ============================================================
# TASK ASSIGNMENT ADMIN
# ============================================================

@admin.register(TaskAssignment)
class TaskAssignmentAdmin(TaskAdminBase):
    list_display = (
        "task",
        "user",
        "status_badge",
        "progress_bar",
        "assigned_by",
        "assigned_at",
        "due_date",
        "completed_at",
    )
    list_filter = ("status", "assigned_at", "completed_at", "task__priority")
    search_fields = (
        "task__task_number",
        "task__title",
        "user__first_name",
        "user__last_name",
        "user__email",
        "assigned_by__first_name",
        "assigned_by__last_name",
    )
    raw_id_fields = ("task", "user", "assigned_by")
    readonly_fields = (
        "assigned_at",
        "accepted_at",
        "started_at",
        "submitted_at",
        "completed_at",
    )
    list_select_related = ("task", "user", "assigned_by")
    list_per_page = 40
    fieldsets = (
        ("Assignment", {
            "fields": ("task", "user", "assigned_by", "status", "progress"),
        }),
        ("Timeline", {
            "fields": (
                "assigned_at",
                "accepted_at",
                "started_at",
                "submitted_at",
                "completed_at",
            ),
        }),
        ("Rejection Details", {
            "fields": ("rejection_note",),
        }),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#d97706",
            "accepted": "#2563eb",
            "in_progress": "#0891b2",
            "on_hold": "#64748b",
            "under_review": "#7c3aed",
            "completed": "#15803d",
            "rejected": "#dc2626",
            "cancelled": "#64748b",
        }
        color = colors.get(obj.status, "#475569")
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description="Progress")
    def progress_bar(self, obj):
        value = obj.progress
        return format_html(
            '<div style="min-width:90px;">'
            '<b>{}%</b><div style="height:6px;background:#e5e7eb;'
            'border-radius:8px;margin-top:4px;"><div style="height:6px;'
            'width:{}%;background:#153030;border-radius:8px;"></div></div></div>',
            value, value,
        )

    @admin.display(description="Task due date", ordering="task__due_date")
    def due_date(self, obj):
        return obj.task.due_date or "—"


# ============================================================
# COMMENTS ADMIN
# ============================================================

@admin.register(TaskComment)
class TaskCommentAdmin(TaskAdminBase):
    list_display = ("task", "user", "comment_preview", "parent", "created_at")
    search_fields = ("task__task_number", "task__title", "user__first_name",
                     "user__last_name", "comment")
    list_filter = ("created_at",)
    raw_id_fields = ("task", "assignment", "parent", "user")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("task", "user", "assignment", "parent")

    @admin.display(description="Comment")
    def comment_preview(self, obj):
        text = obj.comment.strip()
        return text[:100] + ("…" if len(text) > 100 else "")


# ============================================================
# ACTIVITY LOG ADMIN
# ============================================================

@admin.register(TaskActivity)
class TaskActivityAdmin(TaskAdminBase):
    list_display = ("task", "action", "user", "description_preview", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("task__task_number", "task__title", "user__first_name",
                     "user__last_name", "description", "old_value", "new_value")
    raw_id_fields = ("task", "assignment", "user")
    readonly_fields = (
        "task", "assignment", "user", "action", "description",
        "old_value", "new_value", "created_at", "updated_at",
    )
    list_select_related = ("task", "assignment", "user")
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Activity")
    def description_preview(self, obj):
        text = obj.description.strip()
        return text[:100] + ("…" if len(text) > 100 else "")


# ============================================================
# CHECKLIST ADMIN
# ============================================================

@admin.register(TaskChecklist)
class TaskChecklistAdmin(TaskAdminBase):
    list_display = ("task", "title", "completion_badge", "completed_by", "completed_at")
    list_filter = ("is_completed", "created_at")
    search_fields = ("task__task_number", "task__title", "title")
    raw_id_fields = ("task", "completed_by")
    readonly_fields = ("completed_at",)
    list_select_related = ("task", "completed_by")

    @admin.display(description="Completion", boolean=True, ordering="is_completed")
    def completion_badge(self, obj):
        return obj.is_completed


# ============================================================
# DOCUMENT ADMIN
# ============================================================

@admin.register(TaskAttachment)
class TaskAttachmentAdmin(TaskAdminBase):
    list_display = (
        "task",
        "document_number",
        "title",
        "original_filename",
        "version",
        "uploaded_by",
        "replaced_at",
    )
    list_filter = ("replaced_at", "created_at")
    search_fields = (
        "task__task_number",
        "task__title",
        "document_number",
        "title",
        "original_filename",
    )
    raw_id_fields = ("task", "uploaded_by")
    readonly_fields = (
        "document_number",
        "sequence",
        "original_filename",
        "version",
        "replaced_at",
    )
    list_select_related = ("task", "uploaded_by")
