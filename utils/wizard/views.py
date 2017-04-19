import re
from os import path

from django import forms
from django.conf import settings
from django.core.files import storage
from django.utils.translation import ugettext as trans

from formtools.wizard import views as wizard_views, forms as wizard_forms

from utils.forms import fields as utils_fields


class FileStorageNamedUrlSessionWizardView(
    wizard_views.NamedUrlSessionWizardView
):
    file_storage = storage.FileSystemStorage(
        path.join(settings.MEDIA_ROOT, 'temp')
    )
    storage_name = 'utils.wizard.storage.MultiFileSessionStorage'

    def post(self, *args, **kwargs):
        """
        This method handles POST requests.
        The wizard will render either the current step (if form validation
        wasn't successful), the next step (if the current step was stored
        successful) or the done view (if no more steps are available)
        """
        # Look for a wizard_goto_step element in the posted data which
        # contains a valid step name. If one was found, render the requested
        # form. (This makes stepping back a lot easier).
        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            return self.render_goto_step(wizard_goto_step)

        # Check if form was refreshed
        management_form = wizard_forms.ManagementForm(
            self.request.POST, prefix=self.prefix
        )
        if not management_form.is_valid():
            raise forms.ValidationError(
                trans('ManagementForm data is missing or has been tampered.'),
                code='missing_management_form',
            )

        form_current_step = management_form.cleaned_data['current_step']
        form_refreshed = (
            form_current_step != self.steps.current and
            self.storage.current_step is not None
        )
        if form_refreshed:
            # form refreshed, change current step
            self.storage.current_step = form_current_step

        # check for previously uploaded files so we can display them
        #  if the user goes back to this step or refreshes
        new_files = self.request.FILES  # MultiValueDict
        old_files = self.storage.current_step_files  # dict
        # we only want to deal with dict's and ignore MultiValueDict
        files = {}

        field_regexes = []
        form_class = self.form_list[self.steps.current]
        fields = {}
        if hasattr(form_class, 'base_fields'):
            fields = form_class.base_fields
        # else:  # TODO: handle FormSets
        for field_name, field in fields.items():
            if isinstance(field, utils_fields.MultiFileField):
                # get file from widget (<step>-<field_name>_<#>)
                regex = re.compile('{}-{}_\d'.format(
                    self.steps.current, field_name
                ))
                field_regexes.append((field_name, regex))

        if old_files:
            for step_field_name in old_files:
                # add old files
                files[step_field_name] = old_files[step_field_name]

        if new_files:
            for new_files_field_name in new_files:
                found = False
                for field_name, regex in field_regexes:
                    if regex.match(new_files_field_name):
                        # add combined old/new files or just add new files
                        files[field_name] = (
                            files.get(field_name, []) +
                            new_files.getlist(
                                new_files_field_name
                            )
                        )
                        found = True
                        break

                if not found:
                    # another FileField
                    files[new_files_field_name] = new_files.get(
                        new_files_field_name
                    )

        # get the form for the current step
        form = self.get_form(data=self.request.POST, files=files)

        # and try to validate
        if form.is_valid():
            step_files = self.process_step_files(form)

            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(
                self.steps.current, self.process_step(form)
            )
            self.storage.set_step_files(
                self.steps.current, step_files
            )

            # check if the current step is the last step
            if self.steps.current == self.steps.last:
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)
        else:
            step_files = self.process_step_files(form)
            # although the form is invalid, we can save the previously
            #  uploaded files in storage so the user doesn't have to reupload
            self.storage.set_step_files(
                self.steps.current, step_files
            )

        return self.render(form)
