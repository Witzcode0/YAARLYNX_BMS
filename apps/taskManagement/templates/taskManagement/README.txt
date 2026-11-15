YAARLYNX TASK MANAGEMENT TEMPLATES

Copy this folder into your Django templates directory:

templates/taskManagement/

Files:
- _task_styles.html (shared responsive dark-teal styling)
- dashboard.html
- task_list.html
- task_form.html
- task_detail.html
- my_tasks.html
- kanban.html

These templates are written for the supplied task_management_views.py and the
URL names in apps/taskManagement/urls.py discussed in this conversation.

IMPORTANT VIEW CONTEXT ADDITION:
In task_detail(), add this item to the render context dictionary:
    "staff_users": get_task_users(),
This is required by the Add additional staff form in task_detail.html.

Tailwind CSS and Remix Icon classes are used. Your base template should load
Tailwind CSS and Remix Icon, and expose the blocks title, page_heading,
extra_css, and content.

Task form notes:
- Create form supports assigning multiple users and initial document uploads.
- Edit form updates task fields. Manage additional assignments from task detail.
- Upload forms use multipart/form-data and POST with CSRF tokens.
