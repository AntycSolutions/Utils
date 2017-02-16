from django import shortcuts, http
from django.contrib import messages
from django.core import paginator


def _get_paginate_by(request, rows_per_page_var, context=None):
    paginate_by = 5  # default

    if request.session.get(rows_per_page_var, False):
        # previous stored value
        paginate_by = request.session[rows_per_page_var]

    rows_per_page = request.GET.get(rows_per_page_var, '').strip()
    if rows_per_page:
        # new value
        paginate_by = rows_per_page
        request.session[rows_per_page_var] = paginate_by

    if context:
        context[rows_per_page_var] = paginate_by

    return paginate_by


# rows_per_page is usually the result of _get_paginate_by
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
