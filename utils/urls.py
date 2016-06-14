from django.conf import urls

from utils import views

urlpatterns = ''

urls.handler500 = views.server_error
