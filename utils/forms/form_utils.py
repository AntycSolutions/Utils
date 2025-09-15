from django.core import exceptions
from django.forms import models as forms_models, widgets, forms, formsets


def as_div(self):
    "Returns this form rendered as HTML <div>s."
    return self._html_output(
        normal_row=(
            '<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>'
        ),
        error_row='%s',
        row_ender='</div>',
        help_text_html=' <span class="helptext">%s</span>',
        errors_on_separate_row=True,
    )


def as_span(self):
    "Returns this form rendered as HTML <span>s."
    return self._html_output(
        normal_row=(
            '<span%(html_class_attr)s>%(label)s %(field)s%(help_text)s</span>'
        ),
        error_row='%s',
        row_ender='</span>',
        help_text_html=' <span class="helptext">%s</span>',
        errors_on_separate_row=True,
    )


# used in place of a str as a backwards compatible entry in django Media
# that supports specifying shim dependencies for fallbackjs
class MediaStr(str):
    def __new__(cls, *args, **kwargs):
        key = kwargs.pop('key', None)
        shim = kwargs.pop('shim', None)

        instance = super().__new__(cls, *args, **kwargs)

        instance.key = key
        instance.shim = shim

        return instance


class ImproperlyConfigured(Exception):
    '''Deduplicate queryset improperly configured.'''


def _check_field(form, field, field_name):
    if not isinstance(field, forms_models.ModelChoiceField):
        msg = '{} on {} is not an instance of ModelChoiceField'.format(
            field_name, form.__class__.__name__
        )
        raise ImproperlyConfigured(msg)


def set_to_python(field, queryset):
    '''Override field's to_python.

    By overriding to_python further hits on the db are avoided.

    Replacing to_python instead of creating a class that implements to_python
    is sufficient.
    '''

    # closure to pass queryset to field's to_python
    def to_python(self, value):
        if value in self.empty_values:
            return None
        key = self.to_field_name or 'pk'
        try:
            # generator stops iterating on first matching object
            value = next(
                object_
                for object_ in queryset
                # ids/pks are sent as strs
                if str(getattr(object_, key)) == value
            )
        except StopIteration:
            raise exceptions.ValidationError(
                self.error_messages['invalid_choice'], code='invalid_choice'
            )
        return value

    # set to_python as boundmethod on field
    field.to_python = to_python.__get__(field)


def set_field_choices(form, field_name, queryset):
    '''Set field's choices to queryset results.

    By setting choices further hits on the db are avoided.
    '''
    field = form.fields[field_name]

    _check_field(form, field, field_name)

    set_to_python(field, queryset)

    if isinstance(field.widget, widgets.HiddenInput):
        return  # HiddenInputs do not use choices

    pk = form.initial.get(field_name)
    choices = tuple(
        {
            **(
                {"": field.empty_label}
                if field.empty_label is not None
                else {}
            ),  # empty value, empty_label set in ModelChoiceField init
            **(
                {pk: getattr(form.instance, field_name)}  # __str__
                if pk is not None
                else {}
            ),  # initial object
            **{object_.pk: object_ for object_ in queryset},  # default objects
        }.items()
    )
    field.choices = choices


def get_default_field_querysets(form):
    '''Get default field to queryset dict for form or formset.'''
    default_field_querysets = {
        name: field.queryset
        for name, field in form.fields.items()
        # ModelChoiceFields generate queries
        if isinstance(field, forms_models.ModelChoiceField)
    }
    return default_field_querysets


def set_form_choices(
    form,
    field_querysets=None,
    include_default_field_querysets=True,
    cached_default_field_querysets=None,
):
    '''Set a form's fields' choices to a queryset's results.

    cached_default_field_querysets takes precedence over
    include_default_field_querysets.
    '''
    field_querysets = {} if field_querysets is None else field_querysets
    default_field_querysets = (
        (
            get_default_field_querysets(form)
            if include_default_field_querysets
            else {}
        )
        if cached_default_field_querysets is None
        else cached_default_field_querysets
    )
    for field_name, queryset in (
        # py <= 3.5 dict merge
        {**default_field_querysets, **field_querysets}.items()
    ):
        set_field_choices(form, field_name, queryset)


class DeduplicatedQuerySetBaseFormMixin:
    '''Deduplicate querysets base form mixin.

    For checking mro.
    '''


class DeduplicatedQuerySetFormMixin(DeduplicatedQuerySetBaseFormMixin):
    '''Deduplicate querysets for forms mixin.

    Utilize this when form is created outside of view or admin.

    Pass in field_querysets to set custom querysets per field.
    Pass in include_default_field_querysets to not include default field
    querysets for instances of ModelChoiceField.
    '''

    def __init__(
        self,
        *args,
        field_querysets=None,
        include_default_field_querysets=True,
        # py <= 3.5 no trailing comma for kwargs
        **kwargs
    ):
        '''Set form choices after form has been initialized.'''
        super().__init__(*args, **kwargs)
        # fields have now been copied from base_fields
        set_form_choices(
            self,
            field_querysets=field_querysets,
            include_default_field_querysets=include_default_field_querysets,
        )


class DeduplicatedQuerySetFormSetMixin(DeduplicatedQuerySetBaseFormMixin):
    '''Deduplicate querysets for formsets mixin.

    Utilize this when formset is created outside of view or admin.

    Pass in field_querysets to set custom querysets per field.
    Pass in include_default_field_querysets to not include default field
    querysets for instances of ModelChoiceField.
    '''

    def __init__(
        self,
        *args,
        field_querysets=None,
        include_default_field_querysets=True,
        # py <= 3.5 no trailing comma for kwargs
        **kwargs
    ):
        '''Set deduplicate kwargs as attrs for add_fields.'''
        super().__init__(*args, **kwargs)
        self._field_querysets = field_querysets
        self._include_default_field_querysets = include_default_field_querysets

    # we target add_fields as it is always called after initializing a form or
    # empty_form and it overwrites the foreignkey field.
    # this does get called in other places but if configured properly it will
    # result in no additional queries
    def add_fields(self, form, index):
        '''Set form choices after form has been initialized.

        Caches default field querysets when called for the first time.
        '''
        super().add_fields(form, index)
        self._cached_default_field_querysets = (
            self._cached_default_field_querysets
            if hasattr(self, '_cached_default_field_querysets')
            else (
                get_default_field_querysets(form)
                if self._include_default_field_querysets
                else {}
            )
        )
        set_form_choices(
            form,
            field_querysets=self._field_querysets,
            cached_default_field_querysets=(
                self._cached_default_field_querysets
            ),
        )


def _check_mro(class_, class_name):
    if DeduplicatedQuerySetBaseFormMixin in class_.__mro__:
        msg = (
            'Cannot deduplicate an already deduplicated form or formset: {}.'
        ).format(class_name)
        raise ImproperlyConfigured(msg)


def _check_kwargs(object_, kwargs):
    for field in ['field_querysets', 'include_default_field_querysets']:
        if field in kwargs:
            msg = (
                'Do not pass kwarg {} into {} when using'
                ' deduplicate_class/DeduplicatedQuerySetViewMixin.'
                ' Pass kwargs into deduplicate_class call or define relevant'
                ' DeduplicatedQuerySetViewMixin attr/method.'
            ).format(field, object_.__class__.__name__)
            raise ImproperlyConfigured(msg)


def deduplicate_class(
    class_, field_querysets=None, include_default_field_querysets=True
):
    '''Deduplicate querysets for form or formset class inline.

    Utilize this when the class is generated via factory.

    Pass in field_querysets to set custom querysets per field.
    Pass in include_default_field_querysets to not include default field
    querysets for instances of ModelChoiceField.
    '''
    class_name = class_.__name__

    _check_mro(class_, class_name)

    if issubclass(class_, forms.BaseForm):
        base_class = DeduplicatedQuerySetFormMixin
    elif issubclass(class_, formsets.BaseFormSet):
        base_class = DeduplicatedQuerySetFormSetMixin
    else:
        msg = '{} must be a form or formset'.format(class_name)
        raise ImproperlyConfigured(msg)

    # closure to pass our args/kwargs to created class' init args/kwargs
    def __init__(self, *args, **kwargs):
        _check_kwargs(self, kwargs)
        # super arguments required as method defined outside of class
        super(type(self), self).__init__(
            *args,
            field_querysets=field_querysets,
            include_default_field_querysets=include_default_field_querysets,
            **kwargs,
        )

    # create new class
    return type(
        'DeduplicatedQuerySet{}'.format(class_name),
        (base_class, class_),
        # py <= 3.5 dict merge
        {**class_.__dict__, **base_class.__dict__, '__init__': __init__},
    )
