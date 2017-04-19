import itertools

from django import http
from django.contrib import auth
from django.core.files import uploadedfile

from utils.wizard import views as utils_wizard_views

from . import forms as tests_forms, models as tests_models


class CreateUserWizard(
    utils_wizard_views.FileStorageNamedUrlSessionWizardView
):
    USERFILES = 'userfiles'
    USER = 'user'
    form_list = (
        (USERFILES, tests_forms.WizardUserForm),
        (USER, tests_forms.JustUserForm),
    )
    template_name = 'utils/generics/wizard.html'

    def done(self, form_list, form_dict, **kwargs):
        form = form_dict[self.USERFILES]

        user = form.save()

        # has to be here instead of in form in case we need to clear new files
        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        for _file, initial_datum in both:
            if _file == initial_datum:
                if isinstance(_file, uploadedfile.UploadedFile):
                    # form wizard files are temporarily uploaded
                    tests_models.File.objects.create(
                        file=_file, user=user
                    )
                else:
                    # no change
                    # an empty continue is optimized away and coverage.py
                    #  will mark it as unreached, so we noop instead
                    _file
                    continue
            elif _file is False:
                if isinstance(initial_datum, uploadedfile.UploadedFile):
                    # form wizard files are temporarily uploaded
                    if not initial_datum.closed:
                        initial_datum.close()
                    self.file_storage.delete(initial_datum.name)
                else:
                    file = tests_models.File.objects.get(
                        file=initial_datum, user=user
                    )
                    file.file.delete()
                    file.delete()

        file = form.cleaned_data['file']
        if file:
            tests_models.File.objects.create(
                file=file, user=user
            )

        return http.HttpResponse()


class UpdateUserWizard(CreateUserWizard):
    instance = None

    def get_form_instance(self, step):
        if not self.instance:
            User = auth.get_user_model()
            self.instance = User.objects.get(username='test2')

        return self.instance


class CreateUserWizardRequired(
    utils_wizard_views.FileStorageNamedUrlSessionWizardView
):
    USERFILES = 'userfiles'
    USER = 'user'
    form_list = (
        (USERFILES, tests_forms.WizardUserFormRequired),
        (USER, tests_forms.JustUserForm),
    )
    template_name = 'utils/generics/wizard.html'

    def done(self, form_list, form_dict, **kwargs):
        form = form_dict[self.USERFILES]

        user = form.save()

        # has to be here just in case we need to clear new files
        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        for _file, initial_datum in both:
            if _file == initial_datum:
                if isinstance(_file, uploadedfile.UploadedFile):
                    # form wizard files are temporarily uploaded
                    tests_models.File.objects.create(
                        file=_file, user=user
                    )
            elif _file is False:
                if isinstance(initial_datum, uploadedfile.UploadedFile):
                    # form wizard files are temporarily uploaded
                    if not initial_datum.closed:
                        initial_datum.close()
                    self.file_storage.delete(initial_datum.name)

        return http.HttpResponse()


class UpdateUserWizardRequired(CreateUserWizardRequired):
    instance = None

    def get_form_instance(self, step):
        if not self.instance:
            User = auth.get_user_model()
            self.instance = User.objects.get(username='test2')

        return self.instance
