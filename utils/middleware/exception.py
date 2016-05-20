
class ExceptionUserInfoMiddleware(object):
    """
    Adds user details to request context on receiving an exception, so that
    they show up in the error emails.

    Add to settings.MIDDLEWARE_CLASSES and keep it outermost (i.e. on top if
    possible). This allows it to catch exceptions in other middlewares as well.
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
                request.META['USER_USERNAME'] = request.user.username
            if request.user.email:
                request.META['USER_EMAIL'] = request.user.email
            full_name = request.user.get_full_name()
            if full_name:
                request.META['USER_FULL_NAME'] = full_name
