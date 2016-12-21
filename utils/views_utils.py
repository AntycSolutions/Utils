from django import shortcuts, http
from django.contrib import messages
from django.core import paginator
from django.db import models

from utils.search import get_date_query
from utils import search


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


# the newer and better date search but we need the old one for compat
def _get_date_query(
    request, context, df, dt, date_fields
):
    query = models.Q()
    GET = request.GET

    query_date_from_string = GET.get(df, None)
    if query_date_from_string and query_date_from_string.strip():
        context[df] = query_date_from_string

    query_date_to_string = GET.get(dt, None)
    if query_date_to_string and query_date_to_string.strip():
        context[dt] = query_date_to_string

    if query_date_from_string or query_date_to_string:
        try:
            query = search.get_date_query(
                query_date_from_string, query_date_to_string, date_fields
            )
        except search.DoesNotMatchFormat:
            messages.add_message(
                request,
                messages.WARNING,
                "Invalid date. Please use MM/DD/YYYY."
            )

    return query


def _get_query(request, context, q, fields):
    query = models.Q()
    GET = request.GET

    query_string = GET.get(q, None)
    if query_string and query_string.strip():
        context[q] = query_string

        query = search.get_query(query_string, fields)

    return query


def simple_search(
    request,
    context,
    model=None,
    queryset=None,
    query_param=None,
    fields=None,
    date_from_query_param=None,
    date_to_query_param=None,
    date_fields=None
):
    if not model and not queryset:
        raise Exception('Please provide at least one of model or queryset')

    if not fields and not date_fields:
        raise Exception('Please provide at least one of fields or date_fields')

    if not queryset:
        queryset = model.objects.all()

    if fields:
        if not query_param:
            q = 'q'
        else:
            q = query_param

        query = _get_query(request, context, q, fields)
        queryset = queryset.filter(query)

    if date_fields:
        if not date_from_query_param:
            df = 'df'
        else:
            df = date_from_query_param
        if not date_to_query_param:
            dt = 'dt'
        else:
            dt = date_to_query_param

        date_query = _get_date_query(request, context, df, dt, date_fields)
        queryset = queryset.filter(date_query)

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
    queryset_paginator = paginator.Paginator(queryset, rows_per_page)
    try:
        queryset = queryset_paginator.page(page)
    except paginator.PageNotAnInteger:
        queryset = queryset_paginator.page(1)
    except paginator.EmptyPage:
        queryset = queryset_paginator.page(queryset_paginator.num_pages)

    return queryset


class PermissionMixin:
    permissions = None

    def dispatch(self, *args, **kwargs):
        redirect = self.check_permissions()
        if redirect:
            # permission denied
            return redirect
        else:
            return super().dispatch(*args, **kwargs)

    def check_permissions(self):
        user = self.request.user

        permissions = self.get_permissions()

        if isinstance(permissions, dict):
            permissions = [permissions]

        for perm_dict in permissions:
            if not user.has_perm(perm_dict['permission']):
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    perm_dict.get('message', "Permission denied.")
                )

                return shortcuts.redirect(perm_dict.get('redirect', '/'))

    def get_permissions(self):
        if self.permissions is None:
            raise Exception(
                '{class_name} is missing the permissions attribute.'
                ' Define {class_name}.permissions or override'
                ' {0}.get_permissions().'.format(self.__class__.__name__)
            )

        return self.permissions


class AjaxResponseMixin:
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return http.JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.is_ajax():
            data = {
                'pk': self.object.pk,
            }
            return http.JsonResponse(data)
        else:
            return response
