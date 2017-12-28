from .conf import settings


def site(request):
    resp = {
        'utils_settings': settings,
    }

    return resp
