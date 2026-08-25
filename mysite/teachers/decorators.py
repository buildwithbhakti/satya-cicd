from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

from functools import wraps
def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.account_type != 'teacher':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
