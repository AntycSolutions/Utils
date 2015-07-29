import os
import urllib

from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from utils.search import get_date_query


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
        zeroth_ifd, exif_ifd, gps_ifd = piexif.load(filename)

        if piexif.ZerothIFD.Orientation in zeroth_ifd:
            orientation = zeroth_ifd.pop(piexif.ZerothIFD.Orientation)
            exif_bytes = piexif.dump(zeroth_ifd, exif_ifd, gps_ifd)
    except:
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

    response = HttpResponse(thumbnail, 'image/jpeg')
    return response


def _date_search(request, fields, model, queryset=None):
    if not queryset:
        queryset = model.objects.all()

    if (('df' in request.GET) and request.GET['df'].strip()
            and ('dt' in request.GET)
            and request.GET['dt'].strip()):
        query_date_from_string = request.GET['df']
        query_date_to_string = request.GET['dt']
        date_query = get_date_query(
            query_date_from_string, query_date_to_string, fields
        )
        if date_query:
            if queryset:
                queryset = queryset.filter(date_query)
            else:
                queryset = model.objects.filter(date_query)
        else:
            messages.add_message(
                request, messages.WARNING,
                "Invalid date. Please use MM/DD/YYYY."
            )
    elif ('df' in request.GET) and request.GET['df'].strip():
        query_date_from_string = request.GET['df']
        date_query = get_date_query(
            query_date_from_string, None, fields
        )
        if date_query:
            if queryset:
                queryset = queryset.filter(date_query)
            else:
                queryset = model.objects.filter(date_query)
        else:
            messages.add_message(
                request, messages.WARNING,
                "Invalid date. Please use MM/DD/YYYY."
            )
    elif ('dt' in request.GET) and request.GET['dt'].strip():
        query_date_to_string = request.GET['dt']
        date_query = get_date_query(
            None, query_date_to_string, fields
        )
        if date_query:
            if queryset:
                queryset = queryset.filter(date_query)
            else:
                queryset = model.objects.filter(date_query)
        else:
            messages.add_message(
                request, messages.WARNING,
                "Invalid date. Please use MM/DD/YYYY."
            )

    return queryset


def _get_paginate_by(request, rows_per_page_var):
    paginate_by = 5
    if request.session.get(rows_per_page_var, False):
        paginate_by = request.session[rows_per_page_var]
    if (rows_per_page_var in request.GET
            and request.GET[rows_per_page_var].strip()):
        paginate_by = request.GET[rows_per_page_var]
        request.session[rows_per_page_var] = paginate_by

    return paginate_by


def _paginate(request, queryset, page_var, rows_per_page):
    page = request.GET.get(page_var)
    paginator = Paginator(queryset, rows_per_page)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)

    return queryset
