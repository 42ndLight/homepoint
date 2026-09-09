"""
Utility functions for incidents module.
"""

import logging
import requests
import secrets
import time
from django.core.cache import cache
from django.conf import settings

from .models import SmsNotification

logger = logging.getLogger(__name__)

# Reset OTPs stay valid for 6 minutes.
RESET_OTP_TTL = 360
# Minimum time a user must wait before a reset OTP can be resent.
RESET_RESEND_COOLDOWN = 180
# How long a verified-reset grant remains usable to set a new password.
RESET_GRANT_TTL = 300


class OTPCooldownError(Exception):
    """Raised when an OTP resend is attempted before the cooldown expires."""

    def __init__(self, remaining_seconds):
        self.remaining_seconds = remaining_seconds
        super().__init__(f"OTP resend cooldown active: {remaining_seconds}s remaining")


def get_otp_cache_key(intent, phone_number):
    return f"{intent}_otp_{phone_number}"


def get_otp_cooldown_key(intent, phone_number):
    return f"{intent}_otp_cooldown_{phone_number}"


def get_reset_grant_key(token):
    return f"reset_grant_{token}"


def create_reset_grant(phone_number):
    """
    Issues an opaque, single-use token that proves this phone number's OTP
    was just verified. The token (not the phone number or OTP) is what the
    frontend carries from the verify-OTP step to the set-new-password step.
    """
    token = secrets.token_urlsafe(32)
    cache.set(get_reset_grant_key(token), phone_number, timeout=RESET_GRANT_TTL)
    return token


def get_reset_grant_phone(token):
    """Returns the phone number tied to a still-valid reset grant, or None."""
    return cache.get(get_reset_grant_key(token))


def delete_reset_grant(token):
    cache.delete(get_reset_grant_key(token))


def send_at_sms(
    phone_number: str,
    message: str,
    sender_id: str | None = None,
    intent: str | None = None,
) -> bool:
    """
    Send SMS via Africa's Talking API.
    
    Args:
        phone_number: Recipient phone (e.g., "+254712345678")
        message: SMS text content (max ~160 chars)
        sender_id: Optional registered Africa's Talking short code / sender
            ID used to identify who sent the message. Falls back to the
            provider default when not configured.
        intent: Optional purpose of the message, such as ``login`` or
            ``reset``.
    
    Returns:
        True if sent successfully, False otherwise
    """
    username = getattr(settings, 'AT_USERNAME', 'sandbox')
    api_key = getattr(settings, 'AT_API_KEY', '')
    
    if not api_key:
        logger.warning("AT_API_KEY not configured; SMS not sent")
        return False
    
    # Use sandbox or production endpoint
    if username == 'sandbox':
        url = 'https://api.sandbox.africastalking.com/version1/messaging'
    else:
        url = 'https://api.africastalking.com/version1/messaging'
    
    headers = {
        'apiKey': api_key,
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    payload = {
        'username': username,
        'to': phone_number,
        'message': message,
    }
    if sender_id:
        payload['from'] = sender_id
    
    try:
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        recipients = data.get('SMSMessageData', {}).get('Recipients')
        if recipients:
            if isinstance(recipients, list):
                for recipient_data in recipients:
                    if not isinstance(recipient_data, dict):
                        logger.warning("Unexpected AT SMS recipient data: %r", recipient_data)
                        continue

                    provider_message_id = recipient_data.get('messageId') or recipient_data.get('id')
                    if not provider_message_id:
                        logger.warning(
                            "AT SMS response for %s did not include a provider message ID",
                            phone_number,
                        )
                        continue

                    try:
                        SmsNotification.objects.get_or_create(
                            provider_message_id=str(provider_message_id),
                            defaults={
                                'recipient': recipient_data.get('number', phone_number),
                                'intent': intent,
                                'response_metadata': data,
                            },
                        )
                    except Exception:
                        # Delivery tracking must not alter the established send result contract.
                        logger.exception(
                            "Unable to persist AT SMS notification %s", provider_message_id
                        )
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
        else:
            logger.warning(f"SMS failed for {phone_number}: {data}")
            return False
            
    except requests.RequestException as exc:
        logger.exception(f"AT SMS API request failed for {phone_number}: {exc}")
        return False


def generate_and_send_otp(phone_number, intent, cooldown_seconds=None):
    """
    Generates a 6-digit OTP, caches it, and triggers Africa's Talking.
    Intent can be 'login' or 'reset'.

    If cooldown_seconds is given, enforces a resend cooldown for this
    phone_number/intent pair: raises OTPCooldownError (with the remaining
    wait time) instead of generating a new code when one was already sent
    within the cooldown window. The still-valid OTP is left untouched.
    """
    cooldown_key = get_otp_cooldown_key(intent, phone_number)

    if cooldown_seconds:
        cooldown_expiry = cache.get(cooldown_key)
        if cooldown_expiry:
            remaining = int(cooldown_expiry - time.time())
            if remaining > 0:
                raise OTPCooldownError(remaining)

    otp = f"{secrets.randbelow(1_000_000):06d}"
    cache_key = get_otp_cache_key(intent, phone_number)
    ttl = RESET_OTP_TTL if intent == 'reset' else 360

    cache.set(cache_key, otp, timeout=ttl)

    if cooldown_seconds:
        cache.set(cooldown_key, time.time() + cooldown_seconds, timeout=cooldown_seconds)

    logger.info(f"Generated OTP for {phone_number} (intent={intent})")

    sender_id = getattr(settings, 'AT_SENDER_ID', None)
    message = f"Your HomePoint code is {otp}. Valid for 6 minutes. Dont Share Code With AnyOne"
    send_at_sms(phone_number, message, sender_id=sender_id, intent=intent)

    return True
