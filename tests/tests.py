import itertools
from os import path

from django import test, forms
from django.conf import settings
from django.contrib import auth
from django.utils import timezone
from django.core.files import storage, uploadedfile
from django.utils import datastructures

from formtools.wizard.storage import exceptions
from utils.templatetags import update_attrs
from utils.forms import widgets

from . import (
    models as tests_models, forms as tests_forms, views as tests_views
)


class MultiFileFieldTests(test.TestCase):
    def setUp(self):
        # create test objects

        User = auth.get_user_model()
        user = User.objects.create(username='test1', password='password')

        self.test_file = uploadedfile.SimpleUploadedFile(
            'file1.txt', b'content'
        )
        tests_models.File.objects.create(user=user, file=self.test_file)

    def tearDown(self):
        for file in tests_models.File.objects.all():
            file.file.delete()

    def test_models(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        file = tests_models.File.objects.get(user=user)

        self.assertEqual(file.file.name, 'tests/file1.txt')
        self.assertEqual(file.filename(), 'file1.txt')
        self.assertEqual(str(file), file.filename())

    def test_forms(self):
        str(tests_forms.UserForm())
        tests_forms.MultiFileFieldKwargsUserForm()
        tests_forms.MultiFileFieldRequiredForm()

        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        str(tests_forms.UserForm(instance=user))

    def test_bound_data(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        # existing file
        form = tests_forms.UserForm(
            {
                'username': user.username,
                'date_joined': user.date_joined,
                'password': user.password
            },
            instance=user
        )
        for field in form:
            update_attrs.update_attrs(field, 'new_attr:value')

        # no files
        form = tests_forms.UserForm({
            'username': 'test2',
            'date_joined': timezone.now(),
            'password': 'password',
        })
        for field in form:
            update_attrs.update_attrs(field, 'new_attr:value')

    def test_user_form_valid_data(self):
        # create
        form = tests_forms.UserForm({
            'username': 'test2',
            'date_joined': timezone.now(),
            'password': 'password',
        })
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'test2')

        # update
        User = auth.get_user_model()
        user = User.objects.get(username='test1')
        form = tests_forms.UserForm(
            {
                'username': 'test11',
                'date_joined': user.date_joined,
                'password': user.password
            },
            instance=user
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'test11')

    def test_user_form_invalid_data(self):
        form = tests_forms.UserForm({})
        self.assertFalse(form.is_valid())
        required_msgs = ['This field is required.']
        self.assertEqual(form.errors, {
            'username': required_msgs,
            'date_joined': required_msgs,
            'password': required_msgs,
        })

    def test_user_form_valid_files(self):
        # create
        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content3')
        test_file4 = uploadedfile.SimpleUploadedFile('file4.txt', b'content4')
        test_file5 = uploadedfile.SimpleUploadedFile('file5.txt', b'content5')
        test_file6 = uploadedfile.SimpleUploadedFile('file6.txt', b'content6')

        # one file
        form = tests_forms.UserForm(
            {
                'username': 'test2',
                'date_joined': timezone.now(),
                'password': 'password',
            },
            {
                'files_0': test_file2  # subwidget name
            }
        )
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'test2')

        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        for _file, initial_datum in both:
            if initial_datum is LAST_INITIAL:
                file = tests_models.File.objects.create(file=_file, user=user)
                self.assertEqual(file.file.name, 'tests/file2.txt')
                self.assertEqual(file.filename(), 'file2.txt')
                self.assertEqual(str(file), file.filename())

        # multiple files, MultiValueDict
        form = tests_forms.UserForm(
            {
                'username': 'test3',
                'date_joined': timezone.now(),
                'password': 'password',
            },
            # use MultiValueDict to hit MultiFileInput.value_from_datadict
            datastructures.MultiValueDict({
                'files_0': [test_file3, test_file4]  # subwidget name
            })
        )
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'test3')

        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        i = 0
        for _file, initial_datum in both:
            if initial_datum is LAST_INITIAL:
                file = tests_models.File.objects.create(file=_file, user=user)
                if i == 0:
                    self.assertEqual(file.file.name, 'tests/file3.txt')
                    self.assertEqual(file.filename(), 'file3.txt')
                    self.assertEqual(str(file), file.filename())
                elif i == 1:
                    self.assertEqual(file.file.name, 'tests/file4.txt')
                    self.assertEqual(file.filename(), 'file4.txt')
                self.assertEqual(str(file), file.filename())
                i += 1

        # multiple files, dict
        form = tests_forms.UserForm(
            {
                'username': 'test4',
                'date_joined': timezone.now(),
                'password': 'password',
            },
            {
                'files_0': [test_file5, test_file6]  # subwidget name
            }
        )
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'test4')

        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        i = 0
        for _file, initial_datum in both:
            if initial_datum is LAST_INITIAL:
                file = tests_models.File.objects.create(file=_file, user=user)
                if i == 0:
                    self.assertEqual(file.file.name, 'tests/file5.txt')
                    self.assertEqual(file.filename(), 'file5.txt')
                    self.assertEqual(str(file), file.filename())
                elif i == 1:
                    self.assertEqual(file.file.name, 'tests/file6.txt')
                    self.assertEqual(file.filename(), 'file6.txt')
                self.assertEqual(str(file), file.filename())
                i += 1

    def test_multi_file_field_kwargs(self):
        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile(
            'file3.txt', b'exceed_size_QQQQQ'
        )
        test_file4 = uploadedfile.SimpleUploadedFile(
            'file4.txt', b'too_many_files'
        )

        form = tests_forms.MultiFileFieldKwargsUserForm(
            {
                'username': 'test2',
                'date_joined': timezone.now(),
                'password': 'password',
            },
            {
                'files_0': [test_file2, test_file3]  # subwidget name
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'files': ['File file3.txt exceeded maximum upload size.']}
        )

        form = tests_forms.MultiFileFieldKwargsUserForm(
            {
                'username': 'test2',
                'date_joined': timezone.now(),
                'password': 'password',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'files': ['Ensure at least 1 files are uploaded (received 0).']}
        )

        form = tests_forms.MultiFileFieldKwargsUserForm(
            {
                'username': 'test2',
                'date_joined': timezone.now(),
                'password': 'password',
            },
            {
                # subwidget name
                'files_0': [test_file2, test_file3, test_file4]
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {'files': ['Ensure at most 2 files are uploaded (received 3).']}
        )

    def test_multi_file_field_clear(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        form = tests_forms.UserForm(
            {
                'username': 'test1',
                'date_joined': timezone.now(),
                'password': 'password',
                'files_0-clear': True  # subwidget name
            },
            instance=user
        )
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'test1')

        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        for _file, initial_datum in both:
            self.assertFalse(_file)
            if _file is False:
                file = tests_models.File.objects.get(
                    file=initial_datum, user=user
                )
                file.file.delete()
                file.delete()
                with self.assertRaises(tests_models.File.DoesNotExist):
                    tests_models.File.objects.get(user=user)

    def test_multi_file_field_required_clear_error(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        form = tests_forms.MultiFileFieldRequiredForm(
            {
                'username': 'test1',
                'date_joined': timezone.now(),
                'password': 'password',
                'files_0-clear': True  # subwidget name
            },
            instance=user
        )
        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors,
            {'files': ['This field is required.']}
        )

    def test_multi_file_field_required_clear(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        form = tests_forms.MultiFileFieldRequiredForm(
            {
                'username': 'test1',
                'date_joined': timezone.now(),
                'password': 'password',
                'files_0-clear': False  # subwidget name
            },
            instance=user
        )
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertEqual(user.username, 'test1')

        LAST_INITIAL = object()
        both = itertools.zip_longest(
            form.cleaned_data['files'],
            form.initial['files'],
            fillvalue=LAST_INITIAL
        )
        for _file, initial_datum in both:
            self.assertEqual(_file, initial_datum)

    def test_confirm_file_widget_kwargs(self):
        with self.assertRaises(widgets.MissingFormIdException):
            tests_forms.ConfirmMultiFileMultiWidgetKwargsUserForm()

        with self.assertRaises(widgets.MissingFormInstanceException):
            tests_forms.ConfirmMultiFileMultiWidgetKwargs2UserForm()

    def test_multi_file_field_form_invalid_render(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        form = tests_forms.UserForm(
            {
                'username': 'test1',
                'date_joined': timezone.now(),
                'files_0-clear': True
                # missing required password field
            },
            instance=user
        )
        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors,
            {'password': ['This field is required.']}
        )

        rendered_form = str(form)

        displayed_filename = (
            'Current Number of Files: 1<br />1.'
            ' Currently: <a href="tests/file1.txt">tests/file1.txt</a>'
            ' <input checked="checked" id="files_0-clear_id"'
            ' name="files_0-clear" type="checkbox" />'
            ' <label for="files_0-clear_id">Clear</label>'
        )

        self.assertIn(displayed_filename, rendered_form)

    def test_confirm_clearable_file_no_field_name(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        form = tests_forms.ConfirmClearableFileInputRequiredUserForm(
            {
                'username': 'test1',
                'date_joined': timezone.now(),
                'file-clear': True,
                'password': 'password'
            },
            instance=user
        )
        self.assertTrue(form.is_valid())

        file = tests_models.File.objects.get(user=user)

        # because file is required it ignores the clear and returns the file
        self.assertEqual(
            form.cleaned_data['file'],
            file.file
        )

    def test_confirm_clearable_file_no_field_name_clear(self):
        User = auth.get_user_model()
        user = User.objects.get(username='test1')

        form = tests_forms.ConfirmClearableFileInputUserForm(
            {
                'username': 'test1',
                'date_joined': timezone.now(),
                'file-clear': True,
                'password': 'password'
            },
            instance=user
        )
        self.assertTrue(form.is_valid())

        self.assertEqual(
            form.cleaned_data['file'],
            False
        )

        self.assertIn(
            'Are you sure you want to clear tests/file1.txt', str(form)
        )

    def test_multi_file_field_in_wizard(self):
        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')
        test_file4 = uploadedfile.SimpleUploadedFile('file4.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                # subwidget name
                'userfiles-files_0': [test_file2, test_file3, test_file4]
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # load second step
        response = self.client.get('/wizard/create/user/')
        self.assertEqual(response.status_code, 200)

        # go back to first step
        response = self.client.post(
            '/wizard/create/user/',
            {
                # ManagementForm
                'create_user_wizard-current_step': 'user',
                'wizard_goto_step': 'userfiles'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/')
        )

        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Pending: <a href="/media/temp/file2.txt">file2.txt</a>',
            str(response.content)
        )
        self.assertIn(
            'Pending: <a href="/media/temp/file3.txt">file3.txt</a>',
            str(response.content)
        )
        self.assertIn(
            'Pending: <a href="/media/temp/file4.txt">file4.txt</a>',
            str(response.content)
        )

        # submit first step again, clearing file
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                # delete test_file3
                'userfiles-files_1-clear': True  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # submit second/last step
        response = self.client.post(
            '/wizard/create/user/',
            {
                # data
                'user-username': 'test2',
                'user-date_joined': timezone.now(),
                'user-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'user'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/finished/')
        )

        # load finished step
        response = self.client.get('/wizard/create/finished/')
        self.assertEqual(response.status_code, 200)

        # reset
        response = self.client.get('/wizard/create/?reset')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/?reset=')
        )

        files = tests_models.File.objects.filter(user__username='test2')
        self.assertEqual(2, len(files))
        i = 0
        for file in files:
            if i == 0:
                self.assertEqual(file.file.name, 'tests/file2.txt')
                self.assertEqual(file.filename(), 'file2.txt')
            elif i == 1:
                self.assertEqual(file.file.name, 'tests/file4.txt')
                self.assertEqual(file.filename(), 'file4.txt')
            self.assertEqual(str(file), file.filename())
            i += 1

        # update first step
        response = self.client.post(
            '/wizard/update/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'update_user_wizard-current_step': 'userfiles',
                # files
                # delete test_file2
                'userfiles-files_0-clear': True  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/update/user/')
        )

        # update second step
        response = self.client.post(
            '/wizard/update/user/',
            {
                # data
                'user-username': 'test2',
                'user-date_joined': timezone.now(),
                'user-password': 'password',
                # ManagementForm
                'update_user_wizard-current_step': 'user'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/update/finished/')
        )

        # load finished step again
        response = self.client.get('/wizard/update/finished/')
        self.assertEqual(response.status_code, 200)

        files = tests_models.File.objects.filter(user__username='test2')
        self.assertEqual(1, len(files))
        for file in files:
            self.assertEqual(file.file.name, 'tests/file4.txt')
            self.assertEqual(file.filename(), 'file4.txt')
            self.assertEqual(str(file), file.filename())

    def test_multi_file_field_in_wizard_required(self):
        # load first step
        response = self.client.get('/wizard/create_required/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create_required/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard_required-current_step': 'userfiles',
                # files
                'userfiles-files_0': [test_file2, test_file3]  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create_required/user/')
        )

        # load second step
        response = self.client.get('/wizard/create_required/user/')
        self.assertEqual(response.status_code, 200)

        # go back to first step
        response = self.client.post(
            '/wizard/create_required/user/',
            {
                # ManagementForm
                'create_user_wizard_required-current_step': 'user',
                'wizard_goto_step': 'userfiles'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create_required/userfiles/')
        )

        # load first step
        response = self.client.get('/wizard/create_required/userfiles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Pending: <a href="/media/temp/file2.txt">file2.txt</a>',
            str(response.content)
        )
        self.assertIn(
            'Pending: <a href="/media/temp/file3.txt">file3.txt</a>',
            str(response.content)
        )

        # submit first step again, clearing file
        response = self.client.post(
            '/wizard/create_required/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard_required-current_step': 'userfiles',
                # files
                # delete test_file3
                'userfiles-files_1-clear': True  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create_required/user/')
        )

        # submit second/last step
        response = self.client.post(
            '/wizard/create_required/user/',
            {
                # data
                'user-username': 'test2',
                'user-date_joined': timezone.now(),
                'user-password': 'password',
                # ManagementForm
                'create_user_wizard_required-current_step': 'user'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create_required/finished/')
        )

        # load finished step
        response = self.client.get('/wizard/create_required/finished/')
        self.assertEqual(response.status_code, 200)

        # reset
        response = self.client.get('/wizard/create_required/?reset')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            (
                'Location',
                'http://testserver/wizard/create_required/userfiles/?reset='
            )
        )

        files = tests_models.File.objects.filter(user__username='test2')
        self.assertEqual(1, len(files))
        for file in files:
            self.assertEqual(file.file.name, 'tests/file2.txt')
            self.assertEqual(file.filename(), 'file2.txt')
            self.assertEqual(str(file), file.filename())

        # update first step but fail
        response = self.client.post(
            '/wizard/update_required/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'update_user_wizard_required-current_step': 'userfiles',
                # files
                # delete test_file2
                'userfiles-files_0-clear': True  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', str(response.content))

        files = tests_models.File.objects.filter(user__username='test2')
        self.assertEqual(1, len(files))
        for file in files:
            self.assertEqual(file.file.name, 'tests/file2.txt')
            self.assertEqual(file.filename(), 'file2.txt')
            self.assertEqual(str(file), file.filename())

    def test_multi_file_field_in_wizard_multiple_files(self):
        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                'userfiles-files_0': [test_file2, test_file3]  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Pending: <a href="/media/temp/file2.txt">file2.txt</a>',
            str(response.content)
        )
        self.assertIn(
            'Pending: <a href="/media/temp/file3.txt">file3.txt</a>',
            str(response.content)
        )

        # reset
        response = self.client.get('/wizard/create/?reset')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/?reset=')
        )

    def test_no_initial(self):
        # ConfirmClearableMultiFileMultiWidget.decompress() due to no initial
        str(tests_forms.ConfirmClearableMultiFileMultiWidgetNoInitial())

    def test_no_management_form(self):
        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        # submit first step
        with self.assertRaises(forms.ValidationError):
            self.client.post(
                '/wizard/create_required/userfiles/',
                {
                    # data
                    'userfiles-username': 'test2',
                    'userfiles-date_joined': timezone.now(),
                    'userfiles-password': 'password',
                    # missing ManagementForm
                }
            )

    def test_no_file_storage(self):
        # test no file storage set

        tests_views.UpdateUserWizard.file_storage = None

        User = auth.get_user_model()
        user = User.objects.get(username='test1')
        tests_views.UpdateUserWizard.instance = user

        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')

        # submit first step
        with self.assertRaises(exceptions.NoFileStorageConfigured):
            response = self.client.post(
                '/wizard/update/userfiles/',
                {
                    # data
                    'userfiles-username': 'test1',
                    'userfiles-date_joined': timezone.now(),
                    'userfiles-password': 'password',
                    # ManagementForm
                    'update_user_wizard-current_step': 'userfiles',
                    # files
                    # subwidget name
                    'userfiles-files_0': [test_file2, test_file3]
                }
            )

        tests_views.UpdateUserWizard.file_storage = storage.FileSystemStorage(
            path.join(settings.MEDIA_ROOT, 'temp')
        )

        # test no file storage get

        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                'userfiles-files_0': [test_file2, test_file3]  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        tests_views.CreateUserWizard.file_storage = None

        with self.assertRaises(exceptions.NoFileStorageConfigured):
            response = self.client.get('/wizard/create/userfiles/')

        tests_views.CreateUserWizard.file_storage = storage.FileSystemStorage(
            path.join(settings.MEDIA_ROOT, 'temp')
        )

        # reset
        response = self.client.get('/wizard/create/?reset')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/?reset=')
        )

    def test_wizard_form_refreshed(self):
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'user',
                # files
                'userfiles-files_0': [test_file2, test_file3]  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # resubmit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # reset
        response = self.client.get('/wizard/create/?reset')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/?reset=')
        )

    def test_wizard_storage_file_field(self):
        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                'userfiles-file': test_file2  # field name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # submit second/last step
        response = self.client.post(
            '/wizard/create/user/',
            {
                # data
                'user-username': 'test2',
                'user-date_joined': timezone.now(),
                'user-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'user'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/finished/')
        )

        # load finished step
        response = self.client.get('/wizard/create/finished/')
        self.assertEqual(response.status_code, 200)

        # reset
        response = self.client.get('/wizard/create/?reset')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/?reset=')
        )

        files = tests_models.File.objects.filter(user__username='test2')
        self.assertEqual(1, len(files))
        for file in files:
            self.assertEqual(file.file.name, 'tests/file2.txt')
            self.assertEqual(file.filename(), 'file2.txt')
            self.assertEqual(str(file), file.filename())

    def test_multi_file_field_in_wizard_upload_twice(self):
        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)

        test_file2 = uploadedfile.SimpleUploadedFile('file2.txt', b'content')
        test_file3 = uploadedfile.SimpleUploadedFile('file3.txt', b'content')

        # submit first step
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                'userfiles-files_0': [test_file2]  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # load second step
        response = self.client.get('/wizard/create/user/')
        self.assertEqual(response.status_code, 200)

        # go back to first step
        response = self.client.post(
            '/wizard/create/user/',
            {
                # ManagementForm
                'create_user_wizard-current_step': 'user',
                'wizard_goto_step': 'userfiles'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/userfiles/')
        )

        # load first step
        response = self.client.get('/wizard/create/userfiles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Pending:', str(response.content))

        # submit first step again, clearing file
        response = self.client.post(
            '/wizard/create/userfiles/',
            {
                # data
                'userfiles-username': 'test2',
                'userfiles-date_joined': timezone.now(),
                'userfiles-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'userfiles',
                # files
                'userfiles-files_1': [test_file3]  # subwidget name
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/user/')
        )

        # submit second/last step
        response = self.client.post(
            '/wizard/create/user/',
            {
                # data
                'user-username': 'test2',
                'user-date_joined': timezone.now(),
                'user-password': 'password',
                # ManagementForm
                'create_user_wizard-current_step': 'user'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response._headers['location'],
            ('Location', 'http://testserver/wizard/create/finished/')
        )

        # load finished step
        response = self.client.get('/wizard/create/finished/')
        self.assertEqual(response.status_code, 200)

        files = tests_models.File.objects.filter(user__username='test2')
        self.assertEqual(2, len(files))
        i = 0
        for file in files:
            if i == 0:
                self.assertEqual(file.file.name, 'tests/file2.txt')
                self.assertEqual(file.filename(), 'file2.txt')
            elif i == 1:
                self.assertEqual(file.file.name, 'tests/file3.txt')
                self.assertEqual(file.filename(), 'file3.txt')
            self.assertEqual(str(file), file.filename())
            i += 1
