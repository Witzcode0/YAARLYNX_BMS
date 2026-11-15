
import os
import uuid

from pathlib import Path

from django.db import models, transaction
from django.db.models import Max
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.master.models import BaseModel
from apps.accounts.models import UserAccount

from apps.taskManagement.constants import (
    TaskPriority,
    TaskStatus,
    TaskRecurrence,
)


# ============================================================
# TASK CATEGORY
# ============================================================

class TaskCategory(BaseModel):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    color = models.CharField(
        max_length=20,
        default="#153030"
    )

    class Meta:
        db_table = "task_categories"
        ordering = ["name"]
        verbose_name = "Task Category"
        verbose_name_plural = "Task Categories"

    def __str__(self):
        return self.name


# ============================================================
# MAIN TASK
# ============================================================

class Task(BaseModel):

    task_number = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        db_index=True
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks"
    )

    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.CHOICES,
        default=TaskPriority.MEDIUM,
        db_index=True
    )

    start_date = models.DateField(
        null=True,
        blank=True
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        db_index=True
    )

    created_by = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name="created_tasks"
    )

    recurrence = models.CharField(
        max_length=20,
        choices=TaskRecurrence.CHOICES,
        default=TaskRecurrence.NONE
    )

    is_approved = models.BooleanField(
        default=False
    )

    approved_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_tasks"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

        indexes = [
            models.Index(
                fields=["priority", "due_date"]
            ),
            models.Index(
                fields=["created_by", "created_at"]
            ),
        ]

    def __str__(self):
        return f"{self.task_number} - {self.title}"

    def save(self, *args, **kwargs):

        if not self.task_number:
            self.task_number = (
                f"TASK-{timezone.now():%Y%m%d}-"
                f"{uuid.uuid4().hex[:8].upper()}"
            )

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):

        if not self.due_date:
            return False

        if self.due_date >= timezone.localdate():
            return False

        return self.assignments.exclude(
            status__in=[
                TaskStatus.COMPLETED,
                TaskStatus.CANCELLED,
            ]
        ).exists()

    @property
    def assigned_user_count(self):
        return self.assignments.count()

    @property
    def document_count(self):
        return self.attachments.count()

    @property
    def checklist_count(self):
        return self.checklists.count()


# ============================================================
# TASK ASSIGNMENT
# ============================================================

class TaskAssignment(BaseModel):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name="task_assignments"
    )

    assigned_by = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name="assigned_task_records"
    )

    status = models.CharField(
        max_length=20,
        choices=TaskStatus.CHOICES,
        default=TaskStatus.PENDING,
        db_index=True
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ]
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    rejection_note = models.TextField(
        blank=True
    )

    class Meta:
        db_table = "task_assignments"
        ordering = ["-assigned_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["task", "user"],
                name="unique_task_user_assignment"
            )
        ]

        indexes = [
            models.Index(
                fields=["user", "status"]
            ),
            models.Index(
                fields=["task", "status"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.task.task_number} - "
            f"{self.user.full_name}"
        )


# ============================================================
# TASK COMMENT
# ============================================================

class TaskComment(BaseModel):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments"
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name="task_comments"
    )

    comment = models.TextField()

    class Meta:
        db_table = "task_comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment - {self.task.task_number}"


# ============================================================
# TASK ACTIVITY
# ============================================================

class TaskActivity(BaseModel):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    assignment = models.ForeignKey(
        TaskAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities"
    )

    user = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name="task_activities"
    )

    action = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    old_value = models.CharField(
        max_length=255,
        blank=True
    )

    new_value = models.CharField(
        max_length=255,
        blank=True
    )

    class Meta:
        db_table = "task_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return self.action


# ============================================================
# TASK CHECKLIST
# ============================================================

class TaskChecklist(BaseModel):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="checklists"
    )

    title = models.CharField(
        max_length=200
    )

    is_completed = models.BooleanField(
        default=False
    )

    completed_by = models.ForeignKey(
        UserAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_task_checklists"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "task_checklists"
        ordering = ["created_at"]

    def __str__(self):
        return self.title


# ============================================================
# TASK DOCUMENT UPLOAD PATH
# ============================================================

def task_attachment_upload_path(instance, filename):

    extension = Path(filename).suffix.lower()

    task_number = instance.task.task_number
    document_number = instance.document_number
    version = instance.version

    new_filename = (
        f"{task_number}_"
        f"{document_number}_"
        f"V{version:03d}"
        f"{extension}"
    )

    return (
        f"tasks/{task_number}/documents/"
        f"{new_filename}"
    )


# ============================================================
# TASK ATTACHMENT / DOCUMENT MANAGEMENT
# ============================================================

class TaskAttachment(BaseModel):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    document_number = models.CharField(
        max_length=50,
        editable=False
    )

    sequence = models.PositiveIntegerField(
        editable=False
    )

    title = models.CharField(
        max_length=200,
        blank=True
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True
    )

    file = models.FileField(
        upload_to=task_attachment_upload_path
    )

    version = models.PositiveIntegerField(
        default=1,
        editable=False
    )

    uploaded_by = models.ForeignKey(
        UserAccount,
        on_delete=models.PROTECT,
        related_name="task_attachments"
    )

    replaced_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = "task_attachments"
        ordering = ["sequence"]

        verbose_name = "Task Document"
        verbose_name_plural = "Task Documents"

        constraints = [
            models.UniqueConstraint(
                fields=["task", "sequence"],
                name="unique_task_document_sequence"
            ),
            models.UniqueConstraint(
                fields=["task", "document_number"],
                name="unique_task_document_number"
            ),
        ]

        indexes = [
            models.Index(
                fields=["task", "sequence"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.task.task_number} - "
            f"{self.document_number}"
        )

    # --------------------------------------------------------
    # GENERATED FILE NAME
    # --------------------------------------------------------

    @property
    def generated_filename(self):

        if not self.file:
            return ""

        return os.path.basename(self.file.name)

    # --------------------------------------------------------
    # SAVE / CREATE / REPLACE DOCUMENT
    # --------------------------------------------------------

    def save(self, *args, **kwargs):

        old_file_name = None
        old_storage = None

        # Correct way to identify a new model instance.
        is_new = self._state.adding

        # True only when a new file has been uploaded.
        new_file_uploaded = (
            bool(self.file)
            and not self.file._committed
        )

        with transaction.atomic():

            # ================================================
            # EXISTING DOCUMENT - FILE REPLACEMENT
            # ================================================

            if not is_new:

                old_document = (
                    TaskAttachment.objects
                    .filter(pk=self.pk)
                    .values(
                        "file",
                        "version",
                        "sequence",
                        "document_number",
                    )
                    .first()
                )

                if old_document:

                    # Preserve existing document identity.
                    self.sequence = old_document["sequence"]

                    self.document_number = (
                        old_document["document_number"]
                    )

                    # Increase version only when a new file
                    # is actually uploaded.
                    if new_file_uploaded:

                        old_file_name = old_document["file"]

                        old_storage = self.file.storage

                        self.version = (
                            old_document["version"] + 1
                        )

                        self.replaced_at = timezone.now()

            # ================================================
            # NEW DOCUMENT - GENERATE SEQUENCE
            # ================================================

            else:

                if not self.task_id:
                    raise ValueError(
                        "Task must be saved before uploading documents."
                    )

                # Lock the parent task while generating the
                # next document sequence.
                task = (
                    Task.objects
                    .select_for_update()
                    .get(pk=self.task_id)
                )

                self.task = task

                last_sequence = (
                    TaskAttachment.objects
                    .filter(task_id=self.task_id)
                    .aggregate(
                        maximum=Max("sequence")
                    )["maximum"]
                    or 0
                )

                # Generate next sequence.
                self.sequence = last_sequence + 1

                # Generate document number.
                self.document_number = (
                    f"DOC-{self.sequence:03d}"
                )

                # First version of a new document.
                self.version = 1

            # ================================================
            # ORIGINAL FILE NAME
            # ================================================

            if new_file_uploaded:

                self.original_filename = os.path.basename(
                    self.file.name
                )

            # ================================================
            # SAVE DOCUMENT
            # ================================================

            super().save(*args, **kwargs)

            # ================================================
            # DELETE OLD FILE AFTER DATABASE COMMIT
            # ================================================

            if old_file_name and old_storage:

                transaction.on_commit(
                    lambda name=old_file_name,
                    storage=old_storage: storage.delete(name)
                )


# ============================================================
# DELETE PHYSICAL FILE WHEN DOCUMENT RECORD IS DELETED
# ============================================================

@receiver(post_delete, sender=TaskAttachment)
def delete_task_attachment_file(sender, instance, **kwargs):

    if instance.file and instance.file.name:

        file_name = instance.file.name
        storage = instance.file.storage

        transaction.on_commit(
            lambda: storage.delete(file_name)
        )
