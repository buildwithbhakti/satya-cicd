import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from accounts.models import PasswordHistory
from django.contrib.auth.hashers import check_password


class StrongPasswordValidator:
    """
    Enforces that passwords contain at least one uppercase letter,
    one lowercase letter, one digit, and one special character.
    """

    def validate(self, password, user=None):
        errors = []

        if not re.search(r'[A-Z]', password):
            errors.append(_("at least one uppercase letter (A–Z)"))

        if not re.search(r'[a-z]', password):
            errors.append(_("at least one lowercase letter (a–z)"))

        if not re.search(r'\d', password):
            errors.append(_("at least one digit (0–9)"))

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-\[\]\/\\+=;\'`~]', password):
            errors.append(_("at least one special character (e.g. !@#$%^&*)"))

        if errors:
            raise ValidationError(
                _("Your password must contain %(requirements)s."),
                code='password_too_weak',
                params={'requirements': ", ".join(errors)},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )
    

 
PASSWORD_HISTORY_LIMIT = 5  # Number of previous passwords to remember
 
 
class PasswordHistoryValidator:
    """
    Validates that the new password has not been used recently.
    Checks the last PASSWORD_HISTORY_LIMIT passwords for the user.
    """
 
    def __init__(self, history_limit=PASSWORD_HISTORY_LIMIT):
        self.history_limit = history_limit
 
    def validate(self, password, user=None):
        if user is None or user.pk is None:
            return
 
        # Fetch the last N hashed passwords for this user
        recent_passwords = PasswordHistory.objects.filter(
            user=user
        ).order_by('-created_at')[:self.history_limit]
 
        for history_entry in recent_passwords:
            if check_password(password, history_entry.password):
                raise ValidationError(
                    _(
                        f"You cannot reuse any of your last {self.history_limit} passwords. "
                        "Please choose a different password."
                    ),
                    code='password_reuse',
                )
 
    def get_help_text(self):
        return _(
            f"Your password must not be the same as any of your last {self.history_limit} passwords."
            
        )


def save_password_to_history(user):
    """
    Call this BEFORE saving the user's new password.
    Saves the current (old) password hash to PasswordHistory,
    then trims old records beyond the history limit.
    """
    if not user.password:
        return

    # Store the current password in history before it gets changed
    PasswordHistory.objects.create(
        user=user,
        password=user.password  # Already hashed value from the user model
    )

    # Keep only the most recent N password entries per user
    history_ids_to_keep = (
        PasswordHistory.objects
        .filter(user=user)
        .order_by('-created_at')
        .values_list('id', flat=True)[:PASSWORD_HISTORY_LIMIT]
    )

    # Delete older entries beyond the limit
    PasswordHistory.objects.filter(
        user=user
    ).exclude(
        id__in=list(history_ids_to_keep)
    ).delete()