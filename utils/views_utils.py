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
def _get_date_filter(
    request, context, df, dt, date_fields
):
    query = models.Q()
    GET = request.GET
    has_df = (df in GET) and GET[df].strip()
    has_dt = (dt in GET) and GET[dt].strip()
    if has_df and has_dt:
        query_date_from_string = GET[df]
        query_date_to_string = GET[dt]
        context[df] = query_date_from_string
        context[dt] = query_date_to_string
        query = search.get_date_query(
            query_date_from_string, query_date_to_string, date_fields
        )
    elif has_df:
        query_date_from_string = GET[df]
        context[df] = query_date_from_string
        query = search.get_date_query(
            query_date_from_string, None, date_fields
        )
    elif has_dt:
        query_date_to_string = GET[dt]
        context[dt] = query_date_to_string
        query = search.get_date_query(
            None, query_date_to_string, date_fields
        )

    if query is None:
        query = models.Q()
        messages.add_message(
            request,
            messages.WARNING,
            "Invalid date. Please use MM/DD/YYYY."
        )

    return query


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
