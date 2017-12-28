from django.utils import timezone


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        self.update_user(request)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def update_user(self, request):
        user = request.user
        if user.is_authenticated():
            user.last_active = timezone.now()
            user.save()
