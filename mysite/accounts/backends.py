from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authenticate using either username or email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None
        
        try:
            # Try to fetch user by username first
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # If username doesn't exist, try email
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        
        # Check the password
        if user.check_password(password):
            return user
        return None