import os
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

def get_mpesa_access_token():
    cache_key = "mpesa:access_token"  # or add :sandbox/:prod if you switch environments

    token = cache.get(cache_key)
    if token:
        logger.debug("Returning cached M-Pesa access token")
        return token

    # Fallback to empty string to avoid "concatenate str (not "NoneType")" error
    consumer_key = str(settings.MPESA_CONSUMER_KEY or "")
    consumer_secret = str(settings.MPESA_CONSUMER_SECRET or "")
    base_url = str(settings.MPESA_BASE_URL or "").rstrip("/")
    api_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"

    # Support for static IP via proxy (QuotaGuard / Fixie)
    proxy_url = os.environ.get("QUOTAGUARDSTATIC_URL") or os.environ.get("FIXIE_URL")
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    try:
        auth = HTTPBasicAuth(consumer_key, consumer_secret)
        response = requests.get(api_url, auth=auth, proxies=proxies, timeout=10)

        response.raise_for_status()

        data = response.json()
        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)

        if not access_token:
            logger.error(f"M-Pesa token response missing 'access_token': {data}")
            raise ValueError("No access_token in Safaricom response")

        # Cache with buffer (e.g., refresh 5 min early)
        cache_timeout = int(expires_in) - 300
        cache.set(cache_key, access_token, timeout=cache_timeout)

        logger.info(f"M-Pesa access token obtained and cached (expires in ~{expires_in}s)")
        return access_token

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"M-Pesa Auth HTTP error: {http_err} | Response: {response.text}")
        raise MpesaAPIError(f"Safaricom returned {response.status_code}: {response.text}") from http_err

    except requests.exceptions.RequestException as req_err:
        logger.error(f"M-Pesa connection/request failed: {req_err}")
        raise ConnectionError("Failed to reach Safaricom OAuth server") from req_err

    except Exception:
        logger.exception("Unexpected error in M-Pesa token generation")
        raise 



