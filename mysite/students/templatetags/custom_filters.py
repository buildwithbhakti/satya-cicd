from django import template
from django.utils.translation import gettext as _
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def ampm_label(value):
    if not value:
        return value

    from django.utils.translation import gettext as _
    return _("am_label") if value.hour < 12 else _("pm_label")