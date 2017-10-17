import itertools

from django import forms
from django.contrib import auth

from utils.forms import fields as utils_fields, widgets as utils_widgets

from . import models as tests_models


class JustUserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'


class UserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_list = [
            file.file for file in self.instance.file_set.all()
        ]
        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=len(file_list)
            )
        )
        self.initial['files'] = file_list


class WizardUserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField(required=False)
    file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_list = [
            file.file for file in self.instance.file_set.all()
        ]
        files = kwargs.get('files', None)
        if files:  # value can be set to None
            # temp files (UploadedFile) require attr url to be displayed
            for key in files:
                if key == 'files':
                    _file_list = files.get(key)
                    for _file in _file_list:
                        # /media/temp/ (from CreateUserWizard.file_storage)
                        _file.url = '/media/temp/' + _file.name
                        file_list.append(_file)
        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=len(file_list)
            )
        )
        self.initial['files'] = file_list


class WizardUserFormRequired(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_list = [
            file.file for file in self.instance.file_set.all()
        ]
        files = kwargs.get('files', None)
        if files:  # value can be set to None
            # temp files (UploadedFile) require attr url to be displayed
            for key in files:
                if 'files' == key:
                    _file_list = files.get(key)
                    for _file in _file_list:
                        # /media/temp/ (from CreateUserWizard.file_storage)
                        _file.url = '/media/temp/' + _file.name
                        file_list.append(_file)
        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=len(file_list)
            )
        )
        self.initial['files'] = file_list


class MultiFileFieldRequiredForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_list = [
            file.file for file in self.instance.file_set.all()
        ]
        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=len(file_list)
            )
        )
        self.initial['files'] = file_list


class MultiFileFieldKwargsUserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField(
        required=False,
        min_num=1,
        max_num=2,
        max_file_size=14  # b,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_list = [
            file.file for file in self.instance.file_set.all()
        ]
        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=len(file_list)
            )
        )
        self.initial['files'] = file_list


class ConfirmMultiFileMultiWidgetKwargsUserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableFile()
        )


class ConfirmMultiFileMultiWidgetKwargs2UserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableFile(form_id='')
        )


class ConfirmClearableFileInputRequiredUserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file = self.instance.file_set.first().file
        self.fields['file'].widget = (
            utils_widgets.ConfirmClearableFileInput(
                form_id="form_id",
                form=self
            )
        )
        self.initial['file'] = file


class ConfirmClearableFileInputUserForm(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file = self.instance.file_set.first().file
        self.fields['file'].widget = (
            utils_widgets.ConfirmClearableFileInput(
                form_id="form_id",
                form=self
            )
        )
        self.initial['file'] = file


class ConfirmClearableMultiFileMultiWidgetNoInitial(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=0
            )
        )


class UserFormWithSave(forms.ModelForm):
    class Meta:
        model = auth.get_user_model()
        fields = '__all__'

    files = utils_fields.MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        file_list = [
            file.file for file in self.instance.file_set.all()
        ]
        self.fields['files'].widget = (
            utils_widgets.ConfirmClearableMultiFileMultiWidget(
                form_id="form_id",
                form=self,
                field_name='files',
                file_count=len(file_list)
            )
        )
        self.initial['files'] = file_list

    def save(self, commit=True):
        user = super().save(commit=commit)

        LAST_INITIAL = object()
        cleaned_files = self.cleaned_data['files']
        initial_files = self.initial['files']
        both = itertools.zip_longest(
            cleaned_files,
            initial_files,
            fillvalue=LAST_INITIAL
        )
        for _file, initial_datum in both:
            if _file is None:
                raise Exception(
                    'MultiFile: _file is None, ',
                    'initial_datum: {}, '
                    'cleaned_files: {}, initial_files: {}'.format(
                        initial_datum, cleaned_files, initial_files
                    )
                )  # pragma: no cover
            elif _file == initial_datum:
                # no change
                continue
            elif _file is False:
                tests_models.File.objects.get(
                    file=initial_datum, user=user
                ).delete()
            elif initial_datum is LAST_INITIAL:
                tests_models.File.objects.create(
                    file=_file, user=user
                )
            else:
                raise Exception(
                    'MultiFile: Exception, ',
                    '_file: {}, initial_datum: {}, '
                    'cleaned_files: {}, initial_files: {}'.format(
                        _file, initial_datum, cleaned_files, initial_files
                    )
                )  # pragma: no cover

        return user
