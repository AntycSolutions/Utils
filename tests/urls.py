from django.conf import urls

from . import views


create_user_wizard = views.CreateUserWizard.as_view(
    url_name='user_create_step',
    done_step_name='finished'
)
update_user_wizard = views.UpdateUserWizard.as_view(
    url_name='user_update_step',
    done_step_name='finished'
)
create_user_wizard_required = views.CreateUserWizardRequired.as_view(
    url_name='user_create_required_step',
    done_step_name='finished'
)
update_user_wizard_required = views.UpdateUserWizardRequired.as_view(
    url_name='user_update_required_step',
    done_step_name='finished'
)

urlpatterns = [
    urls.url(
        r'^wizard/create/(?P<step>.+)/$',
        create_user_wizard,
        name='user_create_step'
    ),
    urls.url(
        r'^wizard/create/$',
        create_user_wizard,
        name='user_create'
    ),
    urls.url(
        r'^wizard/update/(?P<step>.+)/$',
        update_user_wizard,
        name='user_update_step'
    ),
    urls.url(
        r'^wizard/update/$',
        update_user_wizard,
        name='user_update'
    ),
    urls.url(
        r'^wizard/create_required/(?P<step>.+)/$',
        create_user_wizard_required,
        name='user_create_required_step'
    ),
    urls.url(
        r'^wizard/create_required/$',
        create_user_wizard_required,
        name='user_create_required'
    ),
    urls.url(
        r'^wizard/update_required/(?P<step>.+)/$',
        update_user_wizard_required,
        name='user_update_required_step'
    ),
    urls.url(
        r'^wizard/update_required/$',
        update_user_wizard_required,
        name='user_update_required'
    ),
]
