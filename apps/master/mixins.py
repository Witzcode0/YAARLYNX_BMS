from apps.master.utils import (
    delete_old_file,
    delete_model_file,
)


class FileReplaceMixin:
    """
    Common file management mixin.

    Automatically:

    1. Detects old files
    2. Saves the new file
    3. Deletes replaced old files
    4. Deletes files when the model is deleted
    """

    file_fields = []

    def save(self, *args, **kwargs):

        old_files = {}

        # ==================================================
        # GET OLD FILES
        # ==================================================

        if self.pk:

            try:

                old_instance = self.__class__.objects.get(
                    pk=self.pk
                )

                for field_name in self.file_fields:

                    old_file = getattr(
                        old_instance,
                        field_name,
                        None
                    )

                    old_files[field_name] = old_file

            except self.__class__.DoesNotExist:
                pass

        # ==================================================
        # SAVE OBJECT
        # ==================================================

        super().save(*args, **kwargs)

        # ==================================================
        # DELETE REPLACED FILES
        # ==================================================

        for field_name in self.file_fields:

            old_file = old_files.get(field_name)

            new_file = getattr(
                self,
                field_name,
                None
            )

            if old_file and new_file:

                if old_file.name != new_file.name:

                    delete_old_file(
                        old_file,
                        new_file
                    )

    def delete(self, *args, **kwargs):

        # ==================================================
        # GET FILES BEFORE DELETE
        # ==================================================

        files_to_delete = []

        for field_name in self.file_fields:

            file_field = getattr(
                self,
                field_name,
                None
            )

            if file_field:
                files_to_delete.append(file_field)

        # ==================================================
        # DELETE DATABASE OBJECT
        # ==================================================

        result = super().delete(*args, **kwargs)

        # ==================================================
        # DELETE FILES
        # ==================================================

        for file_field in files_to_delete:

            delete_model_file(
                file_field
            )

        return result