from django.utils import datastructures
from django.utils import six
from django.core.files import uploadedfile

from formtools.wizard.storage import session, exceptions


class MultiFileSessionStorage(session.SessionStorage):
    def set_step_files(self, step, files):
        if files and not self.file_storage:
            raise exceptions.NoFileStorageConfigured(
                "You need to define 'file_storage' in your "
                "wizard view in order to handle file uploads.")

        if step not in self.data[self.step_files_key]:
            self.data[self.step_files_key][step] = {}

        if isinstance(files, datastructures.MultiValueDict):
            for idx, field in enumerate(files):
                field_files = files.getlist(field)
                file_list = []
                for field_file in field_files:
                    file_dict = self._tmp_save(field_file)
                    file_list.append(file_dict)

                self.data[self.step_files_key][step][field] = file_list
        else:
            for field, field_file in six.iteritems(files or {}):
                if isinstance(field_file, list):
                    field_files = field_file
                    file_list = []
                    for field_file in field_files:
                        file_dict = self._tmp_save(field_file)
                        file_list.append(file_dict)
                    file_value = file_list
                else:
                    file_dict = self._tmp_save(field_file)
                    file_value = file_dict

                self.data[self.step_files_key][step][field] = file_value

    def _tmp_save(self, field_file):
        file_storage = self.file_storage
        file_name = field_file.name
        if file_storage.exists(file_name):
            tmp_filename = file_name
        else:
            tmp_filename = self.file_storage.save(file_name, field_file)
        file_dict = {
            'tmp_name': tmp_filename,
            'name': field_file.name,
            'content_type': field_file.content_type,
            'size': field_file.size,
            'charset': field_file.charset
        }

        return file_dict

    def get_step_files(self, step):
        wizard_files = self.data[self.step_files_key].get(step, {})

        if wizard_files and not self.file_storage:
            raise exceptions.NoFileStorageConfigured(
                "You need to define 'file_storage' in your "
                "wizard view in order to handle file uploads.")

        files = {}
        for field, field_value in six.iteritems(wizard_files):
            if isinstance(field_value, list):
                file_list = []
                for field_dict in field_value:
                    _file = self._get_file(step, field, field_dict)
                    file_list.append(_file)
                files[field] = file_list
            else:
                field_dict = field_value
                _file = self._get_file(step, field, field_dict)
                files[field] = _file

        return files or None

    def _get_file(self, step, field, field_dict):
        field_dict = field_dict.copy()
        tmp_name = field_dict.pop('tmp_name')
        if (step, field, tmp_name) not in self._files:
            self._files[(step, field, tmp_name)] = uploadedfile.UploadedFile(
                file=self.file_storage.open(tmp_name), **field_dict
            )
        return self._files[(step, field, tmp_name)]

    def reset(self):
        # Store unused temporary file names in order to delete them
        # at the end of the response cycle through a callback attached in
        # `update_response`.
        wizard_files = self.data[self.step_files_key]
        for step_files in six.itervalues(wizard_files):
            for step_file in six.itervalues(step_files):
                if isinstance(step_file, list):
                    for _file in step_file:
                        self._tmp_files.append(_file['tmp_name'])
                else:
                    self._tmp_files.append(step_file['tmp_name'])
        self.init_data()
