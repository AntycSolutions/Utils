import os
import urllib

from django.conf import settings
from django import http
from django.views.generic import edit
from django.forms import models


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
    except:
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


class InlineFormsetCreateView(edit.CreateView):

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = self.inline_formset()

        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = self.inline_formset(self.request.POST)

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


class InlineFormsetUpdateView(edit.UpdateView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = self.inline_formset(instance=self.object)

        return self.render_to_response(
            self.get_context_data(form=form, formset=formset)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = self.inline_formset(self.request.POST, instance=self.object)

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
