from django.urls import path

from . import views


app_name = "taskManagement"


urlpatterns = [

    # Dashboard
    path(
        "",
        views.task_dashboard,
        name="task_dashboard"
    ),

    # Task listing
    path(
        "list/",
        views.task_list,
        name="task_list"
    ),

    # Create / Edit / Detail
    path(
        "create/",
        views.task_create,
        name="task_create"
    ),

    path(
        "<uuid:task_id>/",
        views.task_detail,
        name="task_detail"
    ),

    path(
        "<uuid:task_id>/edit/",
        views.task_edit,
        name="task_edit"
    ),

    # Assignments
    path(
        "<uuid:task_id>/assign/",
        views.task_add_assignment,
        name="task_add_assignment"
    ),

    path(
        "<uuid:task_id>/assignment/<uuid:assignment_id>/cancel/",
        views.task_cancel_assignment,
        name="task_cancel_assignment"
    ),

    path(
        "assignment/update-status/",
        views.update_task_status,
        name="update_task_status"
    ),

    # Approval
    path(
        "<uuid:task_id>/approve/",
        views.task_approve,
        name="task_approve"
    ),

    path(
        "<uuid:task_id>/revoke-approval/",
        views.task_revoke_approval,
        name="task_revoke_approval"
    ),

    # Staff tasks
    path(
        "my-tasks/",
        views.my_tasks,
        name="my_tasks"
    ),

    # Kanban
    path(
        "kanban/",
        views.task_kanban,
        name="task_kanban"
    ),

    # Delete task
     path(
        "task/<uuid:task_id>/delete/",
        views.task_delete,
        name="task_delete"
    ),

    # Comments
    path(
        "<uuid:task_id>/comment/",
        views.task_add_comment,
        name="task_add_comment"
    ),

    path(
        "<uuid:task_id>/comment/<uuid:comment_id>/delete/",
        views.task_delete_comment,
        name="task_delete_comment"
    ),

    # Checklist
    path(
        "<uuid:task_id>/checklist/add/",
        views.task_add_checklist,
        name="task_add_checklist"
    ),

    path(
        "<uuid:task_id>/checklist/<uuid:checklist_id>/toggle/",
        views.task_toggle_checklist,
        name="task_toggle_checklist"
    ),

    path(
        "<uuid:task_id>/checklist/<uuid:checklist_id>/delete/",
        views.task_delete_checklist,
        name="task_delete_checklist"
    ),

    # Documents
    path(
        "<uuid:task_id>/documents/upload/",
        views.task_upload_documents,
        name="task_upload_documents"
    ),

    path(
        "<uuid:task_id>/documents/<uuid:document_id>/replace/",
        views.task_replace_document,
        name="task_replace_document"
    ),

    path(
        "<uuid:task_id>/documents/<uuid:document_id>/delete/",
        views.task_delete_document,
        name="task_delete_document"
    ),
]