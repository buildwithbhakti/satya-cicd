import nh3

def strip_tags(value: str) -> str:
    """Strip all HTML/script tags from a string using nh3."""
    if isinstance(value, str):
        return nh3.clean(value, tags=set()).strip()
    return value


class SanitizeForm:
    """
    Mixin that automatically strips HTML tags from all
    string fields. Add to any ModelForm to sanitize all fields.
    """
    def full_clean(self):
        if hasattr(self, 'data'):
            self.data = self.data.copy()
            self.data = {
                key: strip_tags(val) if isinstance(val, str) else val
                for key, val in self.data.items()
            }
        super().full_clean()