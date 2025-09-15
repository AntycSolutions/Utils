from utils import views_utils
from utils.forms import form_utils


class DeduplicatedQuerySetAdminMixin(
    views_utils.DeduplicatedQuerySetBaseViewMixin
):
    '''Deduplicate querysets for admin forms and formsets.

    Define field_querysets/get_field_querysets to set custom querysets per
    field.
    Define include_default_field_querysets/get_include_default_field_querysets
    to not include default field querysets for instances of ModelChoiceField.
    '''

    # Both get_form and get_formset can be defined as only one or the other
    # is called depending on the subclass.

    # for ModelAdmin or similar
    def get_form(self, *args, **kwargs):
        '''Override get_form and replace the class with ours.'''
        form_class = super().get_form(*args, **kwargs)
        deduplicated_form_class = form_utils.deduplicate_class(
            form_class,
            field_querysets=self.get_field_querysets(),
            include_default_field_querysets=(
                self.get_include_default_field_querysets()
            ),
        )
        return deduplicated_form_class

    # for TabularInline/StackedInline or similar
    def get_formset(self, *args, **kwargs):
        '''Override get_formset and replace the class with ours.'''
        formset_class = super().get_formset(*args, **kwargs)
        deduplicated_formset_class = form_utils.deduplicate_class(
            formset_class,
            field_querysets=self.get_field_querysets(),
            include_default_field_querysets=(
                self.get_include_default_field_querysets()
            ),
        )
        return deduplicated_formset_class
