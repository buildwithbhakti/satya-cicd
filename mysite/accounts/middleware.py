from django.http import HttpResponseForbidden
from django.template import loader
from django.conf import settings

class RestrictAdminByIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith("/admin/"):
            allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', [])
            client_ip = self.get_client_ip(request)

            if client_ip not in allowed_ips:
                template = loader.get_template('403.html')
                html = template.render(request=request)
                return HttpResponseForbidden(html)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')