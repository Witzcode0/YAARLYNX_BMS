"""Task Management views for YAARLYNX BMS.
Replace apps/taskManagement/views.py with this file.
"""
import os
from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Q, Count, Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from apps.accounts.models import UserAccount
from apps.taskManagement.constants import TaskPriority, TaskStatus, TaskRecurrence
from .models import (
    Task, TaskCategory, TaskAssignment, TaskComment, TaskActivity,
    TaskChecklist, TaskAttachment,
)

LOGIN_URL = "/login/"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv",
    ".png", ".jpg", ".jpeg", ".webp", ".zip", ".txt",
}

# -----------------------------------------------------------------------------
# Authentication and permissions (custom UserAccount session)
# -----------------------------------------------------------------------------
def task_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get("yaarlynx_user_id")
        if not user_id:
            messages.warning(request, "Please login to access Task Management.")
            return redirect(LOGIN_URL)
        try:
            request.user = UserAccount.objects.select_related("role").get(
                pk=user_id, is_active=True
            )
        except (UserAccount.DoesNotExist, ValueError, TypeError, ValidationError):
            request.session.flush()
            messages.error(request, "Your session is invalid. Please login again.")
            return redirect(LOGIN_URL)
        return view_func(request, *args, **kwargs)
    return wrapper


def _role_code(user):
    role = getattr(user, "role", None)
    if not role:
        return ""
    for attr in ("role_code", "code", "name"):
        value = getattr(role, attr, None)
        if value:
            return str(value).strip().upper()
    return str(role).strip().upper()


def is_task_super_admin(user):
    return _role_code(user) in {"SUPER_ADMIN", "SUPERADMIN"}


def is_task_admin(user):
    return _role_code(user) in {"SUPER_ADMIN", "SUPERADMIN", "ADMIN"}


def is_task_staff(user):
    return _role_code(user) == "STAFF"


def check_task_admin(user):
    if not is_task_admin(user):
        raise PermissionDenied("You do not have permission to manage tasks.")


def check_task_access(user, task):
    if is_task_admin(user):
        return True
    if is_task_staff(user) and TaskAssignment.objects.filter(task=task, user=user).exists():
        return True
    raise PermissionDenied("You do not have access to this task.")


def check_assignment_access(user, assignment):
    if is_task_admin(user) or assignment.user_id == user.pk:
        return True
    raise PermissionDenied("You do not have access to this assignment.")

# -----------------------------------------------------------------------------
# Shared helpers
# -----------------------------------------------------------------------------
def get_task_queryset():
    return Task.objects.select_related(
        "category", "created_by", "approved_by"
    ).prefetch_related("assignments__user", "attachments__uploaded_by", "checklists")


def get_assignment_queryset():
    return TaskAssignment.objects.select_related(
        "task", "task__category", "task__created_by", "user", "assigned_by"
    )


def get_task_users():
    # Role code is checked in Python to remain compatible with custom role schemas.
    users = UserAccount.objects.filter(is_active=True).select_related("role")
    return [u for u in users if is_task_staff(u)]


def get_task_categories():
    return TaskCategory.objects.all().order_by("name")


def log_task_activity(task, user, action, description="", assignment=None,
                      old_value="", new_value=""):
    return TaskActivity.objects.create(
        task=task, assignment=assignment, user=user, action=str(action)[:100],
        description=description or "", old_value=str(old_value or "")[:255],
        new_value=str(new_value or "")[:255],
    )


def valid_choice(value, choices):
    return value in {str(v) for v, _ in choices}


def parse_optional_date(value):
    value = (value or "").strip()
    return parse_date(value) if value else None


def validate_upload(upload):
    if not upload:
        return "Please select a file."
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"File type {ext or '(unknown)'} is not allowed."
    if upload.size > MAX_UPLOAD_SIZE:
        return "Each file must be 10 MB or smaller."
    return None


def task_form_context(task=None):
    return {
        "task": task,
        "categories": get_task_categories(),
        "staff_users": get_task_users(),
        "priority_choices": TaskPriority.CHOICES,
        "recurrence_choices": TaskRecurrence.CHOICES,
    }


def redirect_task(task):
    return redirect("taskManagement:task_detail", task_id=task.pk)


def set_status_timestamps(assignment, status):
    now = timezone.now()
    if status == TaskStatus.ACCEPTED and not assignment.accepted_at:
        assignment.accepted_at = now
    if status == TaskStatus.IN_PROGRESS and not assignment.started_at:
        assignment.started_at = now
    if status == TaskStatus.UNDER_REVIEW:
        assignment.submitted_at = now
    if status == TaskStatus.COMPLETED:
        assignment.completed_at = now
        assignment.progress = 100
    elif status != TaskStatus.COMPLETED:
        assignment.completed_at = None

# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------
@task_login_required
def task_dashboard(request):
    check_task_admin(request.user)
    tasks = get_task_queryset()
    assignments = get_assignment_queryset()
    today = timezone.localdate()
    status_summary = [
        {"value": value, "label": label, "count": assignments.filter(status=value).count()}
        for value, label in TaskStatus.CHOICES
    ]
    priority_summary = [
        {"value": value, "label": label, "count": tasks.filter(priority=value).count()}
        for value, label in TaskPriority.CHOICES
    ]
    context = {
        "total_tasks": tasks.count(),
        "approved_tasks": tasks.filter(is_approved=True).count(),
        "pending_approval": tasks.filter(is_approved=False).count(),
        "overdue_tasks": tasks.filter(due_date__lt=today).exclude(
            assignments__status__in=[TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        ).distinct().count(),
        "total_assignments": assignments.count(),
        "completed_assignments": assignments.filter(status=TaskStatus.COMPLETED).count(),
        "in_progress_assignments": assignments.filter(status=TaskStatus.IN_PROGRESS).count(),
        "staff_count": len(get_task_users()),
        "status_summary": status_summary,
        "priority_summary": priority_summary,
        "recent_tasks": tasks.order_by("-created_at")[:8],
        "recent_activities": TaskActivity.objects.select_related(
            "task", "user", "assignment"
        ).order_by("-created_at")[:10],
    }
    return render(request, "taskManagement/dashboard.html", context)

# -----------------------------------------------------------------------------
# Task list, search and filters
# -----------------------------------------------------------------------------
@task_login_required
def task_list(request):
    check_task_admin(request.user)
    tasks = get_task_queryset()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    priority = request.GET.get("priority", "").strip()
    approval = request.GET.get("approval", "").strip()
    due = request.GET.get("due", "").strip()
    if q:
        tasks = tasks.filter(
            Q(task_number__icontains=q) | Q(title__icontains=q) |
            Q(description__icontains=q) | Q(created_by__first_name__icontains=q) |
            Q(created_by__last_name__icontains=q)
        )
    if category:
        tasks = tasks.filter(category_id=category)
    if valid_choice(priority, TaskPriority.CHOICES):
        tasks = tasks.filter(priority=priority)
    if approval == "approved":
        tasks = tasks.filter(is_approved=True)
    elif approval == "pending":
        tasks = tasks.filter(is_approved=False)
    today = timezone.localdate()
    if due == "overdue":
        tasks = tasks.filter(due_date__lt=today).exclude(
            assignments__status__in=[TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        ).distinct()
    elif due == "today":
        tasks = tasks.filter(due_date=today)
    elif due == "upcoming":
        tasks = tasks.filter(due_date__gt=today)
    tasks = tasks.distinct()
    return render(request, "taskManagement/task_list.html", {
        "tasks": tasks, "categories": get_task_categories(),
        "priority_choices": TaskPriority.CHOICES, "search": q,
        "selected_category": category, "selected_priority": priority,
        "selected_approval": approval, "selected_due": due,
        "total_tasks": tasks.count(),
    })

# -----------------------------------------------------------------------------
# Create and edit task
# -----------------------------------------------------------------------------
@task_login_required
def task_create(request):
    check_task_admin(request.user)
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category", "").strip()
        priority = request.POST.get("priority", TaskPriority.MEDIUM)
        recurrence = request.POST.get("recurrence", TaskRecurrence.NONE)
        start_raw = request.POST.get("start_date", "")
        due_raw = request.POST.get("due_date", "")
        start_date, due_date = parse_optional_date(start_raw), parse_optional_date(due_raw)
        user_ids = list(dict.fromkeys(request.POST.getlist("assigned_users")))
        errors = []
        if not title:
            errors.append("Task title is required.")
        if not valid_choice(priority, TaskPriority.CHOICES):
            errors.append("Select a valid priority.")
        if not valid_choice(recurrence, TaskRecurrence.CHOICES):
            errors.append("Select a valid recurrence.")
        if start_raw and not start_date:
            errors.append("Start date is invalid.")
        if due_raw and not due_date:
            errors.append("Due date is invalid.")
        if start_date and due_date and due_date < start_date:
            errors.append("Due date cannot be earlier than start date.")
        category_obj = TaskCategory.objects.filter(pk=category_id).first() if category_id else None
        if category_id and not category_obj:
            errors.append("Selected category is invalid.")
        staff = get_task_users()
        selected_users = [u for u in staff if str(u.pk) in user_ids]
        if len(selected_users) != len(user_ids):
            errors.append("One or more selected staff members are invalid.")
        uploads = request.FILES.getlist("documents")
        for file in uploads:
            err = validate_upload(file)
            if err:
                errors.append(f"{file.name}: {err}")
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, "taskManagement/task_form.html", task_form_context())
        try:
            with transaction.atomic():
                task = Task.objects.create(
                    title=title, description=description, category=category_obj,
                    priority=priority, start_date=start_date, due_date=due_date,
                    recurrence=recurrence, created_by=request.user,
                )
                for staff_user in selected_users:
                    assignment = TaskAssignment.objects.create(
                        task=task, user=staff_user, assigned_by=request.user,
                        status=TaskStatus.PENDING,
                    )
                    log_task_activity(task, request.user, "assigned",
                                      f"Task assigned to {staff_user.full_name}.", assignment)
                for file in uploads:
                    TaskAttachment.objects.create(
                        task=task, file=file,
                        title=os.path.splitext(file.name)[0][:200],
                        uploaded_by=request.user,
                    )
                log_task_activity(task, request.user, "created", "Task created.")
            messages.success(request, f"Task {task.task_number} created successfully.")
            return redirect_task(task)
        except (IntegrityError, ValidationError, ValueError) as exc:
            messages.error(request, f"Unable to create task: {exc}")
    return render(request, "taskManagement/task_form.html", task_form_context())


@task_login_required
def task_edit(request, task_id):
    check_task_admin(request.user)
    task = get_object_or_404(get_task_queryset(), pk=task_id)
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category", "").strip()
        priority = request.POST.get("priority", task.priority)
        recurrence = request.POST.get("recurrence", task.recurrence)
        start_raw, due_raw = request.POST.get("start_date", ""), request.POST.get("due_date", "")
        start_date, due_date = parse_optional_date(start_raw), parse_optional_date(due_raw)
        errors = []
        if not title:
            errors.append("Task title is required.")
        if not valid_choice(priority, TaskPriority.CHOICES):
            errors.append("Select a valid priority.")
        if not valid_choice(recurrence, TaskRecurrence.CHOICES):
            errors.append("Select a valid recurrence.")
        if start_raw and not start_date:
            errors.append("Start date is invalid.")
        if due_raw and not due_date:
            errors.append("Due date is invalid.")
        if start_date and due_date and due_date < start_date:
            errors.append("Due date cannot be earlier than start date.")
        category_obj = TaskCategory.objects.filter(pk=category_id).first() if category_id else None
        if category_id and not category_obj:
            errors.append("Selected category is invalid.")
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, "taskManagement/task_form.html", task_form_context(task))
        old_title, old_priority, old_due = task.title, task.priority, task.due_date
        task.title, task.description, task.category = title, description, category_obj
        task.priority, task.recurrence = priority, recurrence
        task.start_date, task.due_date = start_date, due_date
        task.save()
        if old_title != title:
            log_task_activity(task, request.user, "updated", "Task title updated.",
                              old_value=old_title, new_value=title)
        if old_priority != priority:
            log_task_activity(task, request.user, "updated", "Task priority updated.",
                              old_value=old_priority, new_value=priority)
        if old_due != due_date:
            log_task_activity(task, request.user, "updated", "Task due date updated.",
                              old_value=old_due, new_value=due_date)
        messages.success(request, "Task updated successfully.")
        return redirect_task(task)
    return render(request, "taskManagement/task_form.html", task_form_context(task))

# -----------------------------------------------------------------------------
# Task detail
# -----------------------------------------------------------------------------
@task_login_required
def task_detail(request, task_id):
    task = get_object_or_404(get_task_queryset(), pk=task_id)
    check_task_access(request.user, task)
    assignments = task.assignments.select_related("user", "assigned_by").order_by("-assigned_at")
    comments = task.comments.select_related("user", "assignment", "parent").prefetch_related("replies__user")
    checklists = task.checklists.select_related("completed_by")
    attachments = task.attachments.select_related("uploaded_by")
    total = checklists.count()
    completed = checklists.filter(is_completed=True).count()
    return render(request, "taskManagement/task_detail.html", {
        "task": task, "assignments": assignments, "comments": comments,
        "activities": task.activities.select_related("user", "assignment")[:50],
        "checklists": checklists, "attachments": attachments,
        "total_checklist": total, "completed_checklist": completed,
        "checklist_percentage": round(completed * 100 / total) if total else 0,
        "is_task_admin": is_task_admin(request.user),
        "my_assignment": assignments.filter(user=request.user).first(),
        "status_choices": TaskStatus.CHOICES,
    })

# -----------------------------------------------------------------------------
# Assignment management
# -----------------------------------------------------------------------------
@task_login_required
@require_POST
def task_add_assignment(request, task_id):
    check_task_admin(request.user)
    task = get_object_or_404(Task, pk=task_id)
    ids = list(dict.fromkeys(request.POST.getlist("assigned_users")))
    staff = [u for u in get_task_users() if str(u.pk) in ids]
    if not ids:
        messages.warning(request, "Select at least one staff member.")
        return redirect_task(task)
    if len(staff) != len(ids):
        messages.error(request, "One or more selected staff members are invalid.")
        return redirect_task(task)
    added = 0
    with transaction.atomic():
        for user in staff:
            assignment, created = TaskAssignment.objects.get_or_create(
                task=task, user=user,
                defaults={"assigned_by": request.user, "status": TaskStatus.PENDING},
            )
            if created:
                added += 1
                log_task_activity(task, request.user, "assigned",
                                  f"Task assigned to {user.full_name}.", assignment)
            elif assignment.status == TaskStatus.CANCELLED:
                assignment.status = TaskStatus.PENDING
                assignment.assigned_by = request.user
                assignment.rejection_note = ""
                assignment.save()
                log_task_activity(task, request.user, "reassigned",
                                  f"Task reassigned to {user.full_name}.", assignment,
                                  old_value=TaskStatus.CANCELLED, new_value=TaskStatus.PENDING)
    messages.success(request, f"{added} new assignment(s) added.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_cancel_assignment(request, task_id, assignment_id):
    check_task_admin(request.user)
    task = get_object_or_404(Task, pk=task_id)
    assignment = get_object_or_404(TaskAssignment, pk=assignment_id, task=task)
    if assignment.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
        messages.info(request, "Assignment is already completed or cancelled.")
    else:
        old = assignment.status
        assignment.status = TaskStatus.CANCELLED
        assignment.save()
        log_task_activity(task, request.user, "cancelled", "Assignment cancelled.",
                          assignment, old_value=old, new_value=TaskStatus.CANCELLED)
        messages.success(request, "Assignment cancelled.")
    return redirect_task(task)

# -----------------------------------------------------------------------------
# Status and progress update
# -----------------------------------------------------------------------------
@task_login_required
@require_POST
def update_task_status(request):
    assignment = get_object_or_404(get_assignment_queryset(), pk=request.POST.get("assignment_id"))
    check_assignment_access(request.user, assignment)
    status = request.POST.get("status", "").strip()
    if not valid_choice(status, TaskStatus.CHOICES):
        messages.error(request, "Invalid task status.")
        return redirect_task(assignment.task)
    if status in {TaskStatus.COMPLETED, TaskStatus.REJECTED, TaskStatus.CANCELLED} and not is_task_admin(request.user):
        messages.error(request, "Only an administrator can set this status.")
        return redirect_task(assignment.task)
    note = request.POST.get("rejection_note", "").strip()
    if status == TaskStatus.REJECTED and not note:
        messages.error(request, "Please provide a rejection reason.")
        return redirect_task(assignment.task)
    old_status, old_progress = assignment.status, assignment.progress
    raw_progress = request.POST.get("progress", "").strip()
    if raw_progress:
        try:
            progress = int(raw_progress)
            if not 0 <= progress <= 100:
                raise ValueError
        except ValueError:
            messages.error(request, "Progress must be between 0 and 100.")
            return redirect_task(assignment.task)
        assignment.progress = progress
    assignment.status = status
    assignment.rejection_note = note if status == TaskStatus.REJECTED else ""
    set_status_timestamps(assignment, status)
    assignment.save()
    if old_status != assignment.status:
        log_task_activity(assignment.task, request.user, "status_updated",
                          "Assignment status changed.", assignment,
                          old_value=old_status, new_value=assignment.status)
    if old_progress != assignment.progress:
        log_task_activity(assignment.task, request.user, "progress_updated",
                          "Assignment progress updated.", assignment,
                          old_value=old_progress, new_value=assignment.progress)
    messages.success(request, "Task assignment updated successfully.")
    return redirect_task(assignment.task)

# -----------------------------------------------------------------------------
# My tasks and Kanban board
# -----------------------------------------------------------------------------
@task_login_required
def my_tasks(request):
    if is_task_admin(request.user):
        assignments = get_assignment_queryset()
        selected_user = request.GET.get("user", "").strip()
        if selected_user:
            assignments = assignments.filter(user_id=selected_user)
    elif is_task_staff(request.user):
        assignments = get_assignment_queryset().filter(user=request.user)
        selected_user = ""
    else:
        raise PermissionDenied("You do not have access to My Tasks.")
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    q = request.GET.get("q", "").strip()
    if valid_choice(status, TaskStatus.CHOICES):
        assignments = assignments.filter(status=status)
    if valid_choice(priority, TaskPriority.CHOICES):
        assignments = assignments.filter(task__priority=priority)
    if q:
        assignments = assignments.filter(Q(task__title__icontains=q) | Q(task__task_number__icontains=q))
    return render(request, "taskManagement/my_tasks.html", {
        "assignments": assignments, "status_choices": TaskStatus.CHOICES,
        "priority_choices": TaskPriority.CHOICES,
        "staff_users": get_task_users() if is_task_admin(request.user) else [],
        "selected_user": selected_user, "selected_status": status,
        "selected_priority": priority, "search": q,
        "is_task_admin": is_task_admin(request.user),
    })


@task_login_required
def task_kanban(request):
    if is_task_admin(request.user):
        assignments = get_assignment_queryset()
    elif is_task_staff(request.user):
        assignments = get_assignment_queryset().filter(user=request.user)
    else:
        raise PermissionDenied("You do not have access to the Kanban board.")
    q = request.GET.get("q", "").strip()
    if q:
        assignments = assignments.filter(
            Q(task__title__icontains=q) | Q(task__task_number__icontains=q) |
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
        )
    columns = [{
        "value": value, "label": label,
        "assignments": assignments.filter(status=value).order_by("-assigned_at"),
    } for value, label in TaskStatus.CHOICES]
    return render(request, "taskManagement/kanban.html", {
        "kanban_columns": columns, "status_choices": TaskStatus.CHOICES,
        "total_assignments": assignments.count(),
        "is_task_admin": is_task_admin(request.user), "search": q,
    })

# -----------------------------------------------------------------------------
# Comments and threaded replies
# -----------------------------------------------------------------------------
@task_login_required
@require_POST
def task_add_comment(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    check_task_access(request.user, task)
    text = request.POST.get("comment", "").strip()
    parent_id = request.POST.get("parent_id", "").strip()
    assignment_id = request.POST.get("assignment_id", "").strip()
    if not text:
        messages.error(request, "Comment cannot be empty.")
        return redirect_task(task)
    parent = get_object_or_404(TaskComment, pk=parent_id, task=task) if parent_id else None
    assignment = get_object_or_404(TaskAssignment, pk=assignment_id, task=task) if assignment_id else None
    if assignment:
        check_assignment_access(request.user, assignment)
    TaskComment.objects.create(task=task, assignment=assignment, parent=parent,
                               user=request.user, comment=text)
    log_task_activity(task, request.user, "comment_added", "A comment was added.", assignment)
    messages.success(request, "Comment added.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_delete_comment(request, task_id, comment_id):
    task = get_object_or_404(Task, pk=task_id)
    comment = get_object_or_404(TaskComment, pk=comment_id, task=task)
    check_task_access(request.user, task)
    if not is_task_admin(request.user) and comment.user_id != request.user.pk:
        raise PermissionDenied("You can delete only your own comments.")
    comment.delete()
    log_task_activity(task, request.user, "comment_deleted", "A comment was deleted.")
    messages.success(request, "Comment deleted.")
    return redirect_task(task)

# -----------------------------------------------------------------------------
# Checklist management
# -----------------------------------------------------------------------------
@task_login_required
@require_POST
def task_add_checklist(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    check_task_access(request.user, task)
    title = request.POST.get("title", "").strip()
    if not title:
        messages.error(request, "Checklist title is required.")
        return redirect_task(task)
    item = TaskChecklist.objects.create(task=task, title=title)
    log_task_activity(task, request.user, "checklist_added", f"Checklist added: {item.title}")
    messages.success(request, "Checklist item added.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_toggle_checklist(request, task_id, checklist_id):
    task = get_object_or_404(Task, pk=task_id)
    check_task_access(request.user, task)
    item = get_object_or_404(TaskChecklist, pk=checklist_id, task=task)
    item.is_completed = not item.is_completed
    item.completed_by = request.user if item.is_completed else None
    item.completed_at = timezone.now() if item.is_completed else None
    item.save()
    log_task_activity(task, request.user, "checklist_updated",
                      f"Checklist {'completed' if item.is_completed else 'reopened'}: {item.title}")
    messages.success(request, "Checklist updated.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_delete_checklist(request, task_id, checklist_id):
    check_task_admin(request.user)
    task = get_object_or_404(Task, pk=task_id)
    item = get_object_or_404(TaskChecklist, pk=checklist_id, task=task)
    title = item.title
    item.delete()
    log_task_activity(task, request.user, "checklist_deleted", f"Checklist deleted: {title}")
    messages.success(request, "Checklist item deleted.")
    return redirect_task(task)

# -----------------------------------------------------------------------------
# Task documents: upload, replace, delete
# -----------------------------------------------------------------------------
@task_login_required
@require_POST
def task_upload_documents(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    check_task_access(request.user, task)
    uploads = request.FILES.getlist("documents")
    if not uploads and request.FILES.get("file"):
        uploads = [request.FILES["file"]]
    if not uploads:
        messages.error(request, "Select at least one document.")
        return redirect_task(task)
    errors = [f"{f.name}: {err}" for f in uploads if (err := validate_upload(f))]
    if errors:
        for err in errors:
            messages.error(request, err)
        return redirect_task(task)
    with transaction.atomic():
        for file in uploads:
            doc = TaskAttachment.objects.create(
                task=task, file=file, title=os.path.splitext(file.name)[0][:200],
                uploaded_by=request.user,
            )
            log_task_activity(task, request.user, "documents_uploaded",
                              f"Document {doc.document_number} uploaded.")
    messages.success(request, f"{len(uploads)} document(s) uploaded.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_replace_document(request, task_id, document_id):
    task = get_object_or_404(Task, pk=task_id)
    check_task_access(request.user, task)
    doc = get_object_or_404(TaskAttachment, pk=document_id, task=task)
    upload = request.FILES.get("file")
    error = validate_upload(upload)
    if error:
        messages.error(request, error)
        return redirect_task(task)
    old_version = doc.version
    doc.file = upload
    doc.uploaded_by = request.user
    doc.save()  # TaskAttachment.save() increments version and replaces old storage file.
    log_task_activity(task, request.user, "document_replaced",
                      f"{doc.document_number} replaced with V{doc.version}.",
                      old_value=f"V{old_version}", new_value=f"V{doc.version}")
    messages.success(request, "Document replaced successfully.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_delete_document(request, task_id, document_id):
    task = get_object_or_404(Task, pk=task_id)
    check_task_access(request.user, task)
    doc = get_object_or_404(TaskAttachment, pk=document_id, task=task)
    if not is_task_admin(request.user) and doc.uploaded_by_id != request.user.pk:
        raise PermissionDenied("You can delete only documents uploaded by you.")
    number = doc.document_number
    doc.delete()
    log_task_activity(task, request.user, "document_deleted", f"Document {number} deleted.")
    messages.success(request, "Document deleted.")
    return redirect_task(task)

# -----------------------------------------------------------------------------
# Task approval
# -----------------------------------------------------------------------------
@task_login_required
@require_POST
def task_approve(request, task_id):
    check_task_admin(request.user)
    task = get_object_or_404(Task, pk=task_id)
    if task.is_approved:
        messages.info(request, "Task is already approved.")
    else:
        task.is_approved = True
        task.approved_by = request.user
        task.approved_at = timezone.now()
        task.save()
        log_task_activity(task, request.user, "approved", "Task approved.")
        messages.success(request, "Task approved successfully.")
    return redirect_task(task)


@task_login_required
@require_POST
def task_revoke_approval(request, task_id):
    check_task_admin(request.user)
    task = get_object_or_404(Task, pk=task_id)
    if not task.is_approved:
        messages.info(request, "Task is not currently approved.")
    else:
        task.is_approved = False
        task.approved_by = None
        task.approved_at = None
        task.save()
        log_task_activity(task, request.user, "approval_revoked", "Task approval revoked.")
        messages.success(request, "Task approval revoked.")
    return redirect_task(task)
