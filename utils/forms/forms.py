import itertools

from django import forms
from django.forms import models as forms_models
from django.contrib.auth import forms as auth_forms


class BaseNestedFormSet(forms.BaseInlineFormSet):

    def add_fields(self, form, index):
        super(BaseNestedFormSet, self).add_fields(form, index)

        form.nested = self.nested_formset_class(
            instance=form.instance,
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None,
            prefix='%s-%s' % (
                form.prefix,
                self.nested_formset_class.get_default_prefix()
            ),
        )

    def is_valid(self):
        result = super(BaseNestedFormSet, self).is_valid()

        if self.is_bound:
            for form in self.forms:
                if not self._should_delete_form(form):
                    result = result and form.nested.is_valid()

        return result

    def save(self, commit=True):
        result = super(BaseNestedFormSet, self).save(commit=commit)

        nested_result_list = []
        for form in self.forms:
            if not self._should_delete_form(form):
                nested_result = form.nested.save(commit=commit)
                if nested_result:
                    nested_result_list.append(nested_result)

        result_tuples = []
        for r, nr in itertools.zip_longest(result, nested_result_list):
            result_tuples.append((r, nr))

        return result_tuples

    @property
    def media(self):
        return self.empty_form.media + self.empty_form.nested.media


class BaseNestedModelForm(forms.ModelForm):

    def has_changed(self):
        return (
            super(BaseNestedModelForm, self).has_changed() or
            self.nested.has_changed()
        )


class MinimumInlineFormSet(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(MinimumInlineFormSet, self).__init__(*args, **kwargs)

        if not hasattr(self, 'minimum'):
            self.minimum = 1
        if not hasattr(self, 'minimum_name'):
            self.minimum_name = self.model.__name__

    def clean(self):
        super(MinimumInlineFormSet, self).clean()

        count = 0
        for form in self.forms:
            try:
                if (
                    form.cleaned_data and
                    not form.cleaned_data.get('DELETE', False)
                        ):
                    count += 1
            except AttributeError:
                # Invalid subform raises AttributeError for cleaned_data
                pass

        if (count < self.minimum) and self.validate_minimum:
            raise forms.ValidationError(
                'Please add at least %s %s%s.' % (
                    self.minimum, self.minimum_name,
                    '' if self.minimum == 1 else 's'
                )
            )


class MinimumNestedFormSet(BaseNestedFormSet):

    def __init__(self, *args, **kwargs):
        super(MinimumNestedFormSet, self).__init__(*args, **kwargs)

        if not hasattr(self, 'minimum'):
            self.minimum = 1
        if not hasattr(self, 'minimum_name'):
            self.minimum_name = self.model.__name__

    def clean(self):
        count = 0
        for form in self.forms:
            try:
                form.nested.validate_minimum = False
                if (
                    form.cleaned_data and
                    not form.cleaned_data.get('DELETE', False)
                        ):
                    count += 1
                    if form.cleaned_data['id'] or form.has_changed():
                        form.nested.validate_minimum = True
            except AttributeError:
                # Invalid subform raises AttributeError for cleaned_data
                pass

        if count < self.minimum:
            raise forms.ValidationError(
                'Please add at least %s %s%s.' % (
                    self.minimum, self.minimum_name,
                    '' if self.minimum == 1 else 's'
                )
            )

        super(MinimumNestedFormSet, self).clean()


def nestedformset_factory(parent_model, child_model, nested_formset, **kwargs):
    if 'formset' not in kwargs:
        kwargs['formset'] = BaseNestedFormSet
    if 'form' not in kwargs:
        kwargs['form'] = BaseNestedModelForm

    NestedFormSet = forms_models.inlineformset_factory(
        parent_model,
        child_model,
        **kwargs
    )
    NestedFormSet.nested_formset_class = nested_formset

    return NestedFormSet  # Is class, not instance


def minimum_nestedformset_factory(
        parent_model, model, nested_formset,
        minimum=1, minimum_name=None,
        minimum_nested=1, minimum_name_nested=None,
        **kwargs):
    if 'formset' not in kwargs:
        kwargs['formset'] = MinimumNestedFormSet
    if 'form' not in kwargs:
        kwargs['form'] = BaseNestedModelForm

    NestedFormSet = forms_models.inlineformset_factory(
        parent_model,
        model,
        **kwargs
    )
    NestedFormSet.nested_formset_class = nested_formset

    if not hasattr(NestedFormSet, 'minimum'):
        NestedFormSet.minimum = minimum
    if not hasattr(NestedFormSet, 'minimum_name'):
        NestedFormSet.minimum_name = minimum_name
    if not hasattr(NestedFormSet.nested_formset_class, 'minimum'):
        NestedFormSet.nested_formset_class.minimum = (
            minimum_nested or model.__name__
        )
    if not hasattr(NestedFormSet.nested_formset_class, 'minimum_name'):
        NestedFormSet.nested_formset_class.minimum_name = (
            minimum_name_nested or nested_formset.model.__name__
        )

    return NestedFormSet  # Is class, not instance


class AuthenticationForm(auth_forms.AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['autofocus'] = True
