# PSL
import json
# 3rd Party
from django import http
from django.utils import deprecation
# Local
from utils import utils


if not hasattr(deprecation, 'MiddlewareMixin'):
    deprecation.MiddlewareMixin = object  # django <= 1.8 compat


# compatible with both styles of middleware
class ExceptionUserInfoMiddleware(deprecation.MiddlewareMixin):
    """
    Adds user details to request context on receiving an exception,
    so that they show up in the error emails.

    Add to settings.MIDDLEWARE (1.11) or
    settings.MIDDLEWARE_CLASSES (<1.11) and keep it outermost
    (i.e. on top if possible). This allows it to catch exceptions
    in other middlewares as well.
    """

    def process_exception(self, request, exception):
        """
        Process the exception.

        :Parameters:
           - `request`: request that caused the exception
           - `exception`: actual exception being raised
        """

        if request.user.is_authenticated():
            if request.user.username:
                request.META['!!_USER_USERNAME'] = request.user.username
            if request.user.email:
                request.META['!!_USER_EMAIL'] = request.user.email
            full_name = request.user.get_full_name()
            if full_name:
                request.META['!!_USER_FULL_NAME'] = full_name

        branch, commit_hash = utils.get_git_info()
        request.META['!!_PY_BRANCH'] = branch
        request.META['!!_PY_COMMIT'] = commit_hash

        if hasattr(request, 'content_type'):
            content_type = request.content_type
        else:
            content_type = request.META.get('CONTENT_TYPE')
        if request.is_ajax() or 'json' in content_type:
            try:
                body = request.body.decode()
            except http.request.UnreadablePostError:
                request.META['!!_ERROR'] = 'UnreadablePostError'
                return
            if not body:
                request.META['!!_ERROR'] = 'no body'
                return
            try:
                event = json.loads(body)
            except json.JSONDecodeError:
                request.META['!!_ERROR'] = 'JSONDecodeError'
                return
            if not event:
                request.META['!!_ERROR'] = 'no json'
                return
            config_name = event.get('config_name')
            if config_name:
                request.META['!!_CONFIG'] = config_name
            request.META['!!_JSON'] = json.dumps(event, sort_keys=True)
