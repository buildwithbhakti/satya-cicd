# evaluate/utils/encrypt.py
from django.db import models
from django.conf import settings
from cryptography.fernet import InvalidToken

class EncryptedTextField(models.TextField):

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return settings.FERNET.decrypt(value.encode()).decode()
        except (InvalidToken, Exception):
            # plain text row (not yet encrypted) — return as-is
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        # avoid double-encrypting already encrypted values
        try:
            settings.FERNET.decrypt(value.encode())
            return value  # already encrypted, skip
        except (InvalidToken, Exception):
            return settings.FERNET.encrypt(value.encode()).decode()