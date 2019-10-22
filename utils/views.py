import os
import json
import urllib

from django.conf import settings
from django import http, template
from django.template import loader
from django.views.generic import edit
from django.forms import models
from django.views.decorators import csrf
from django.core import mail
from django.contrib.auth import decorators


def _get_exif(filename):
    import piexif
    # from PIL.ExifTags import TAGS

    orientation = None
    exif_bytes = None

    # exifinfo = img._getexif()
    # if exifinfo is not None:
    #     ret = {}
    #     for tag, value in exifinfo.items():
    #         decoded = TAGS.get(tag, tag)
    #         ret[decoded] = value
    #     for k, v in ret.items():
    #         if k == "Orientation":
    #             orientation = v

    try:
        exif_dict = piexif.load(filename)

        zeroth = '0th'
        exif = 'Exif'
        gps = 'GPS'

        zeroth_ifd = exif_dict[zeroth]
        exif_ifd = exif_dict[exif]
        gps_ifd = exif_dict[gps]

        if piexif.ImageIFD.Orientation in zeroth_ifd:
            orientation = zeroth_ifd.pop(piexif.ImageIFD.Orientation)
            new_exif_dict = {zeroth: zeroth_ifd, exif: exif_ifd, gps: gps_ifd}
            exif_bytes = piexif.dump(new_exif_dict)
    except ValueError:  # Given file is niether JPEG nor TIFF.
        orientation = None
        exif_bytes = None

    return orientation, exif_bytes


def _update_orientation(img, orientation):
    from PIL import Image

    if orientation == 2:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 3:
        img = img.rotate(180)
    elif orientation == 4:
        img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 5:
        img = img.rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 6:
        img = img.rotate(-90)
    elif orientation == 7:
        img = img.rotate(90).transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 8:
        img = img.rotate(90)

    return img


def _rescale(input_file, width, height, force=True):
    from PIL import Image
    from PIL import ImageOps
    from io import BytesIO

    try:
        max_width = int(width)
        max_height = int(height)
    except TypeError:
        return None

    img = Image.open(input_file)
    if not force:
        img.thumbnail((max_width, max_height), Image.ANTIALIAS)
    else:
        img = ImageOps.fit(img, (max_width, max_height,),
                           method=Image.ANTIALIAS)

    tmp = BytesIO()
    orientation, exif_bytes = _get_exif(input_file)
    if orientation:
        img = _update_orientation(img, orientation)
        img.save(tmp, 'JPEG', exif=exif_bytes)
    else:
        if img.mode != 'RGB':
            img.convert('RGB').save(tmp, 'JPEG')
        else:
            img.save(tmp, 'JPEG')
    tmp.seek(0)
    output_data = tmp.getvalue()
    img.close()
    tmp.close()

    return output_data


def get_thumbnail(request, width, height, url):
    decoded_url = urllib.parse.unquote(url)
    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    partial_path = decoded_url.replace(media_url, "")
    path = os.path.join(media_root, partial_path)
    thumbnail = None
    if os.path.isfile(path):
        thumbnail = _rescale(path, width, height, force=False)

    response = http.HttpResponse(thumbnail, 'image/jpeg')

    return response


class FormsetUpdateView(edit.UpdateView):
    can_delete = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'form' in context:
            formset = context.pop('form')
            context['formset'] = formset

        return context

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if 'instance' in kwargs:
            queryset = kwargs.pop('instance')
            kwargs['queryset'] = queryset

        return kwargs

    def get_form_class(self):
        if self.form_class:
            return self.form_class

        form_class = models.modelformset_factory(self.model, fields='__all__',
                                                 can_delete=self.can_delete)

        return form_class


class InlineFormSetCreateView(edit.CreateView):
    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = self.get_inline_formset()

        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = self.get_inline_formset(
            self.request.POST, self.request.FILES
        )

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        formset.instance = self.object
        formset.save()

        return http.HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


class InlineFormSetUpdateView(edit.UpdateView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = self.get_inline_formset(instance=self.object)

        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = self.get_inline_formset(
            self.request.POST, self.request.FILES, instance=self.object
        )

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        self.object = form.save()
        formset.save()

        return http.HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formset):
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )


def raise_exception(request):
    # for testing 500s, exceptions, and error emails
    if 'json' in request.GET:
        request.content_type = 'json'
        body = b'''{
            "test_json": 1,
            "str": "asdf",
            "dt": "2019-04-17T21:19:19.857Z",
            "dec": 1.2345
        }'''
        request._body = request.body or body
    raise Exception('Intentional error: raise_exception')


@csrf.requires_csrf_token
def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: :template:`500.html`
    Context: None (switched to RequestContext so we can load css)
    """
    try:
        _template = loader.get_template(template_name)
    except template.TemplateDoesNotExist:
        if template_name != '500.html':
            # Reraise if it's a missing custom template.
            raise

        return http.HttpResponseServerError(
            '<h1>Server Error (500)</h1>', content_type='text/html'
        )

    return http.HttpResponseServerError(
        _template.render(template.RequestContext(request))
    )


@decorators.login_required
def js_reporter(request):
    if request.method == 'POST':
        url = request.POST.get('url', '')
        _json = request.POST.get('json', '{}')
        response = request.POST.get('response', '')

        if url or _json or response:
            pretty_json = json.dumps(json.loads(_json), indent=4)
            # preserve spaces and newlines
            pretty_html_json = " &nbsp;".join(
                pretty_json.replace('\n', '<br>').split('  ')
            )
            mail.mail_admins(
                'JS Issue',
                'url: {}\n\njson:\n\n{}\n\nresponse:\n\n{}\n\n'.format(
                    url, pretty_json, response
                ),
                html_message=(
                    'url: {}<br><br>'
                    'json:<br><br><code>{}</code><br><br>'
                    'response:<br><br>{}<br><br>'.format(
                        url,
                        pretty_html_json,
                        response.replace('\n', '<br>')
                    )
                )
            )

    return http.JsonResponse({})


def get_git_info():
    git_info = os.popen(
        'cd "{}" &&'
        ' git symbolic-ref --short HEAD &&'
        ' git rev-parse HEAD'.format(settings.BASE_DIR)
    ).read().replace('\n', ' ').strip().split(' ')

    if len(git_info) < 2 or not git_info[0] or not git_info[1]:
        return 'Invalid git info', str(git_info)

    branch = git_info[0]
    commit_hash = git_info[1]

    return branch, commit_hash


def git_commit(request):
    branch, commit_hash = get_git_info()

    return http.JsonResponse({'branch': branch, 'commit': commit_hash})
