# utils/mixins.py
import hmac
import hashlib
import json
from django.conf import settings


class compute_signature:
    """Simple HMAC signature mixin"""
    
    SIGNABLE_FIELDS = []
    
    def _get_signable_data(self):
        """Get data to sign as a string"""
        data = {}
        for field in self.SIGNABLE_FIELDS:
            value = getattr(self, field)
            if hasattr(value, 'pk'):  # ForeignKey
                data[field] = value.pk
            else:
                data[field] = str(value) if value is not None else ''
        
        return json.dumps(data, sort_keys=True)
    
    def generate_signature(self):
        """Generate HMAC signature"""
        data = self._get_signable_data()
        return hmac.new(
            settings.SECRET_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self):
        """Check if signature is valid"""
        if not self.signature:
            return False
        return hmac.compare_digest(self.signature, self.generate_signature())