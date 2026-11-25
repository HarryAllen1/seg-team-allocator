from typing import ClassVar

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    SetPasswordMixin,
    UserCreationForm,
)

from .models import User


class BootstrapFormMixin:
    """Add Bootstrap's CSS classes to the input widgets of a form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class LogInForm(BootstrapFormMixin, AuthenticationForm):
    """Form to log in with a username and password."""


class PasswordForm(BootstrapFormMixin, PasswordChangeForm):
    """Form for a logged in user to change their own password."""

    # Replace Django's new_password1 and new_password2 fields with clearer names.
    new_password1 = None  # pyright: ignore[reportIncompatibleVariableOverride, reportAssignmentType]
    new_password2 = None  # pyright: ignore[reportIncompatibleVariableOverride, reportAssignmentType]
    new_password, new_password_confirmation = SetPasswordMixin.create_password_fields(
        label1='New password', label2='New password confirmation'
    )
    def __init__(self, *args, **kwargs):
        self.field_order = ('old_password', 'new_password', 'new_password_confirmation')
        super().__init__(*args, **kwargs)

    def clean(self):
        self.validate_passwords('new_password', 'new_password_confirmation')
        self.validate_password_for_user(self.user, 'new_password_confirmation')
        return super().clean()

    def save(self, commit=True):
        return self.set_password_and_save(self.user, 'new_password', commit=commit)


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Form for a logged in user to edit their own profile."""

    class Meta:
        model = User
        fields: ClassVar[list[str]] = ['username', 'first_name', 'last_name', 'email']


class UserCreateForm(BootstrapFormMixin, UserCreationForm):
    """Form for a superuser to create a new user, including a password."""

    # Replace Django's password1 and password2 fields with clearer names.
    password1 = None
    password2 = None
    password, password_confirmation = SetPasswordMixin.create_password_fields()

    class Meta:
        model = User
        fields: ClassVar[list[str]] = ['username', 'first_name', 'last_name', 'email', 'is_superuser']

    def validate_passwords(self, password1_field_name='password', password2_field_name='password_confirmation'):
        super().validate_passwords(password1_field_name, password2_field_name)

    def validate_password_for_user(self, user, password_field_name='password_confirmation'):
        super().validate_password_for_user(user, password_field_name)

    def set_password_and_save(self, user, password_field_name='password', commit=True):
        return super().set_password_and_save(user, password_field_name, commit)


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    """Form for a superuser to update the details of any user."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('gender', 'ethnicity', 'c_score', 'workload'):
            self.fields[field_name].required = False

    def clean_gender(self):
        value = self.cleaned_data.get('gender')
        return self.instance.gender if value is None else value

    def clean_ethnicity(self):
        value = self.cleaned_data.get('ethnicity')
        return self.instance.ethnicity if value is None else value

    def clean_c_score(self):
        return self.cleaned_data.get('c_score')

    def clean_workload(self):
        value = self.cleaned_data.get('workload')
        return self.instance.workload if value is None else value

    class Meta:
        model = User
        fields: ClassVar[list[str]] = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_superuser',
            'gender',
            'ethnicity',
            'c_score',
            'committed',
            'workload',
        ]

# Rejects a name that does not end in .csv and a file larger than 2 MB, with a readable message
# (Note: File size is not too necessary and may be removed)
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB is far more than ~300 students need
class CohortUploadForm(BootstrapFormMixin, forms.Form):
    """Form for a logged in user to upload a cohort CSV file."""

    file = forms.FileField(
        label='Cohort CSV file',
        help_text='One row per student. Required columns: first_name, last_name, email.',
        widget=forms.ClearableFileInput(attrs={'accept': '.csv,text/csv'}),
    )

    def clean_file(self):
        upload = self.cleaned_data['file']
        if not upload.name.lower().endswith('.csv'):
            raise forms.ValidationError('Please upload a file with a .csv extension.')
        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError('The file is larger than 2 MB. Check that it is the right file.')
        return upload
