"""
Manual reCAPTCHA verification using `requests` instead of django_recaptcha's
built-in urllib-based client.

Why this exists: on Python 3.10, urllib.request.ProxyHandler does not
reliably support HTTPS-front proxies (i.e. a proxy that itself requires a
TLS-wrapped connection, as opposed to a plain-TCP proxy that only tunnels
TLS traffic through a CONNECT request). This causes urlopen() to fail with
"Connection reset by peer" even though the proxy and network path are fine.

`requests` (via urllib3) handles this correctly regardless of Python
version, so we use it directly here instead of relying on
django_recaptcha.client.submit().

Reuses the same RECAPTCHA_PROXY / RECAPTCHA_DOMAIN / RECAPTCHA_PRIVATE_KEY
settings you already have configured for django_recaptcha - no new settings
needed.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_RECAPTCHA_DOMAIN = "www.google.com"
VERIFY_TIMEOUT_SECONDS = 10


def verify_recaptcha(token, remote_ip=None):
    """
    Verify a reCAPTCHA response token against Google's siteverify API.

    Args:
        token: the value of the 'g-recaptcha-response' field submitted by
               the widget/JS on the frontend.
        remote_ip: optional, the end user's IP address (request.META
               .get('REMOTE_ADDR')) - passed through to Google, purely
               informational on their end.

    Returns:
        (success: bool, error_codes: list[str])
    """
    if not token:
        return False, ["missing-input-response"]

    domain = getattr(settings, "RECAPTCHA_DOMAIN", DEFAULT_RECAPTCHA_DOMAIN)
    private_key = settings.RECAPTCHA_PRIVATE_KEY
    proxies = getattr(settings, "RECAPTCHA_PROXY", None)

    url = f"https://{domain}/recaptcha/api/siteverify"
    payload = {
        "secret": private_key,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        resp = requests.post(
            url,
            data=payload,
            proxies=proxies,
            timeout=VERIFY_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.RequestException as e:
        # Network/proxy/timeout/SSL error talking to Google - fail closed,
        # but log it distinctly from a "bad token" failure so it's easy to
        # tell apart in your error logs / monitoring.
        logger.error("reCAPTCHA verification request failed: %s", e)
        return False, ["connection-error"]
    except ValueError:
        logger.error("reCAPTCHA verification returned non-JSON response: %s", resp.text)
        return False, ["invalid-response-format"]

    success = result.get("success", False)
    error_codes = result.get("error-codes", [])

    if not success:
        logger.warning("reCAPTCHA verification failed: %s", error_codes)

    return success, error_codes
