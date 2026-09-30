import os

from django.conf import settings


# ============================================================
# STORAGE PREFIX
# ============================================================

def get_storage_prefix():
    """
    DEBUG=True  -> LOCAL_
    DEBUG=False -> LIVE_
    """

    return "LOCAL_" if settings.DEBUG else "LIVE_"


# ============================================================
# INSTANCE FILE PATH
# ============================================================

def get_instance_file_path(path, instance, filename):
    """
    Generate upload path using instance ID.

    Example:

        DEBUG=True
        LOCAL_users/profile/<instance.id>.jpg

        DEBUG=False
        LIVE_users/profile/<instance.id>.jpg
    """

    extension = os.path.splitext(filename)[1].lower()

    prefix = get_storage_prefix()

    path = path.strip("/")

    return f"{prefix}{path}/{instance.id}{extension}"


# ============================================================
# DELETE OLD FILE
# ============================================================

def delete_old_file(old_file, new_file=None):
    """
    Delete old file when it is replaced.

    Default files are never deleted.
    """

    if not old_file:
        return

    if not old_file.name:
        return

    # Never delete default files
    if old_file.name.startswith("default/"):
        return

    # Same file -> nothing to delete
    if new_file and old_file.name == new_file.name:
        return

    try:

        if old_file.storage.exists(old_file.name):
            old_file.storage.delete(old_file.name)

    except Exception:
        pass


# ============================================================
# DELETE MODEL FILE
# ============================================================

def delete_model_file(file_field):
    """
    Delete a file when the model itself is deleted.
    """

    if not file_field:
        return

    if not file_field.name:
        return

    # Never delete default files
    if file_field.name.startswith("default/"):
        return

    try:

        if file_field.storage.exists(file_field.name):
            file_field.storage.delete(file_field.name)

    except Exception:
        pass