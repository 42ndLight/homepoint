"""
Utility functions for incidents module.
"""

import logging
import requests
import random
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


def send_at_sms(phone_number: str, message: str) -> bool:
    """
    Send SMS via Africa's Talking API.
    
    Args:
        phone_number: Recipient phone (e.g., "+254712345678")
        message: SMS text content (max ~160 chars)
    
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
    
    try:
        resp = requests.post(url, headers=headers, data=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if data.get('SMSMessageData', {}).get('Recipients'):
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
        else:
            logger.warning(f"SMS failed for {phone_number}: {data}")
            return False
            
    except requests.RequestException as exc:
        logger.exception(f"AT SMS API request failed for {phone_number}: {exc}")
        return False

def generate_and_send_otp(phone_number, intent):
    """
    Generates a 6-digit OTP, caches it for 6 minutes, and triggers Africa's Talking.
    Intent can be 'login' or 'reset'.
    """
    otp = str(random.randint(100000, 999999))
    cache_key = f"{intent}_otp_{phone_number}"
    
    # Store OTP in cache for 360 seconds (6 minutes)
    cache.set(cache_key, otp, timeout=360)
    
    # Print for debugging since we are in sandbox mode
    print(f"[DEBUG] Generated OTP for {phone_number} ({intent}): {otp}")
    logger.info(f"[DEBUG] Generated OTP for {phone_number} ({intent}): {otp}")
    
    # Trigger Africa's Talking SMS logic here
    message = f"Your HomePoint code is {otp}. Valid for 6 minutes."
    send_at_sms(phone_number, message)
    
    return True
