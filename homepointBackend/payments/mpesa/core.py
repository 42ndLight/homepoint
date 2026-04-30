import requests
import base64
from datetime import datetime
import json
import logging
from django.conf import settings
from payments.mpesa.utils import get_mpesa_access_token

logger = logging.getLogger(__name__)

class MpesaExpressClient:
    """
    Utility for M-Pesa Express (STK Push) interactions.
    Inspired by core.py but integrated with project settings and utilities.
    """

    def __init__(self):
        self.base_url = settings.MPESA_BASE_URL
        self.shortcode = settings.MPESA_SHORTCODE
        # Default passkey for sandbox if not in settings
        self.passkey = settings.MPESA_PASSKEY
        # Use NGROK_URL from settings for the callback
        self.callback_url = f"{settings.NGROK_URL}/payments/stk-callback/" if hasattr(settings, 'NGROK_URL') and settings.NGROK_URL else ""

    def stk_push(self, phone_number, amount, order_id, transaction_desc="Order Payment"):
        """
        Initiate an STK Push to a customer's phone.
        """
        access_token = get_mpesa_access_token()
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((self.shortcode + self.passkey + timestamp).encode('ascii')).decode('utf-8')
        
        # Format phone number: ensure it starts with 254
        formatted_phone = phone_number
        if formatted_phone.startswith('0'):
            formatted_phone = '254' + formatted_phone[1:]
        elif formatted_phone.startswith('+'):
            formatted_phone = formatted_phone[1:]
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(float(amount)), # Ensure it's an integer
            'PartyA': formatted_phone,
            'PartyB': self.shortcode,
            'PhoneNumber': formatted_phone,
            'CallBackURL': self.callback_url,
            'AccountReference': f"Order{order_id}",
            'TransactionDesc': transaction_desc
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        try:
            logger.info(f"Initiating STK Push for Order #{order_id} to {formatted_phone}")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push request failed for Order #{order_id}: {str(e)}")
            raise

    def parse_stk_result(self, result_data):
        """
        Parse the result of Lipa na MPESA Online Payment (STK Push)
        """
        data = {}
        callback = result_data.get('Body', {}).get('stkCallback', {})
        data['ResultCode'] = callback.get('ResultCode')
        data['ResultDesc'] = callback.get('ResultDesc')
        data['MerchantRequestID'] = callback.get('MerchantRequestID')
        data['CheckoutRequestID'] = callback.get('CheckoutRequestID')
        
        metadata = callback.get('CallbackMetadata')
        if metadata:
            metadata_items = metadata.get('Item', [])
            for item in metadata_items:
                data[item['Name']] = item.get('Value')
        
        return data
