from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from accounts.utils.sanitizer import SanitizeForm
from .models import CustomUser, Institute
from django_recaptcha.fields import ReCaptchaField
from django.utils.translation import gettext_lazy as _ 
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from disposable_email_domains import blocklist
import dns.resolver
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm

from accounts.utils.password_validators import PasswordHistoryValidator
from accounts.utils.recaptcha_utils import verify_recaptcha
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django.conf import settings


validator_alphabet_msg = _("(Can only contain alphabets)")
validator_address_msg = _("(No special characters allowed)")

phone_validator = RegexValidator(
        regex=r'^\d{10}$',
        message=_('Enter a valid 10-digit phone number.'),
    )

alphabets_and_space = RegexValidator(
        regex=r'^[a-zA-Z\s]+$',
        message=validator_alphabet_msg,
        code='invalid_format'
    )

address_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9\s,.-]+$',
        message=validator_address_msg,
        code='invalid_format'
    )

def validate_email_domain(email):
    domain = email.split('@')[-1].lower()

    # 1. Check blocklist
    if domain in blocklist:
        raise ValidationError("Disposable email addresses are not allowed.")

    # 2. Check MX records
    try:
        dns.resolver.resolve(domain, 'MX')
    except Exception:
        raise ValidationError("Email domain has no valid mail server.")

class CustomUserCreationForm(SanitizeForm, UserCreationForm):

    username = forms.CharField(
        error_messages={
            "unique": _("A user with that username already exists."),
        }
    )

    phone = forms.CharField(
        max_length=10,
        required=False,
        validators=[phone_validator]
    )

    city = forms.CharField(
        validators=[alphabets_and_space],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid city name. ") + validator_alphabet_msg,
        }
    )

    address = forms.CharField(
        validators=[address_validator],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid address. ") + validator_address_msg,
        }
    )

    email = forms.EmailField(required=True, validators=[validate_email_domain])

    captcha = forms.CharField(
        widget=ReCaptchaV2Checkbox(
            attrs={'data-sitekey': settings.RECAPTCHA_PUBLIC_KEY,},
        ),
        required=True,
    )
    institute = forms.ModelChoiceField(
            queryset=Institute.objects.all(),
            required=True,
            empty_label="Select Institute",
        )
    
    class Meta:
        model = CustomUser
        fields = ("account_type", "username", "first_name", "last_name", "email", "gender", "phone", "city", "address", "password1", "password2","standard", "institute", "captcha")
        error_messages = {
            'password_mismatch': _("The two password fields did not match."),
        }

    def clean_captcha(self):
        # Skip ReCaptchaField's own validate() (which calls the broken
        # urllib-based client.submit() internally) and verify manually.
        token = self.data.get('g-recaptcha-response')
        success, error_codes = verify_recaptcha(token)
        if not success:
            raise forms.ValidationError(f"reCAPTCHA verification failed: {error_codes}")
        return self.cleaned_data.get('captcha')
    
    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            # Remove default Django error first
            if "password2" in self.errors:
                del self.errors["password2"]

            # Add your translated error
            self.add_error(
                "password2",
                ValidationError(
                    _("The two password fields did not match."),
                    code="password_mismatch"
                )
            )

        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username")

    # captcha = ReCaptchaField()


    error_messages = {
    'invalid_login': "Invalid username/email or password. Please try again.",
    'inactive': "This account is inactive.", 
    }

    # def clean(self):
    #     # By this point, field-level validation (including captcha) has already run,
    #     # so self.errors already reflects any captcha failure.
    #     if self.errors.get('captcha'):
    #         # Don't touch credentials at all — no authenticate() call,
    #         # no invalid_login message. Only the captcha error is shown.
    #         return self.cleaned_data

    #     # Captcha passed — now it's safe to check credentials normally.
    #     return super().clean()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username","first_name","last_name","email","gender","phone","city","address","standard","institute", "exam_mode")
    
    email = forms.EmailField(required=True, validators=[validate_email_domain])

    city = forms.CharField(
        validators=[alphabets_and_space],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid city name. ") + validator_alphabet_msg,
        }
    )

    address = forms.CharField(
        validators=[address_validator],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid address. ") + validator_address_msg,
        }
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists() and self.instance.email != email:
            raise forms.ValidationError(_("User with this email already exists."))
        return email

class InstituteForm(SanitizeForm, forms.ModelForm):

    name = forms.CharField(
        validators=[address_validator],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid name. ") + validator_address_msg,
        }
    )

    phone = forms.CharField(
        max_length=10,
        validators=[phone_validator],
        required=False,
    )

    def clean_website(self):
        website = self.cleaned_data.get('website', '')
        if website:
            # Only allow http/https URLs
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(website)
            except forms.ValidationError:
                raise forms.ValidationError("Enter a valid URL starting with http:// or https://")
        return website.strip()
    
    affiliation = forms.CharField(
        validators=[alphabets_and_space],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid affiliation. ") + validator_alphabet_msg,
        }
    )

    address = forms.CharField(
        validators=[address_validator],
        required=False,
        error_messages={
            "invalid_format": _("Enter a valid address. ") + validator_address_msg,
        }
    )
    
    captcha = ReCaptchaField()

    class Meta:
        model = Institute
        fields = ("name", "affiliation", "address", "phone", "website", "captcha")



class HistoryAwarePasswordChangeForm(PasswordChangeForm):
    """
    Extends Django's built-in PasswordChangeForm to also block
    passwords that were used recently (stored in PasswordHistory).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = (
            password_validation.password_validators_help_text_html()
        )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )

        # Run history validation explicitly with user context
        validator = PasswordHistoryValidator()
        validator.validate(password1, user=self.user)

        # Run all other AUTH_PASSWORD_VALIDATORS
        password_validation.validate_password(password1, self.user)

        return password2


class HistoryAwareSetPasswordForm(SetPasswordForm):
    """
    Extends Django's SetPasswordForm (used in admin or password reset)
    to also block recently used passwords.
    """

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )

        # Run history validation with user context
        validator = PasswordHistoryValidator()
        validator.validate(password1, user=self.user)

        # Run all other AUTH_PASSWORD_VALIDATORS
        password_validation.validate_password(password1, self.user)

        return password2