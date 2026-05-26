import requests
import hmac
import hashlib
from django.conf import settings
from typing import Dict, Optional
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)


class PaystackClient:
    """
    Utility for Paystack payment interactions.
    Handles initialization, verification, and webhook validation.
    """
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
    
    def initialize_transaction(
        self,
        amount: int,
        email: str,
        reference: str,
        metadata: Optional[Dict] = None,
        callback_url: Optional[str] = None,
    ) -> Dict:
        """
        Initialize a Paystack transaction.
        
        Args:
            amount: Amount in smallest currency unit (kobo for NGN, cents for others)
            email: Customer's email address
            reference: Unique transaction reference
            metadata: Optional metadata (customer info, order details)
            callback_url: URL to redirect after payment
            
        Returns:
            Dict with 'status', 'authorization_url', 'access_code', 'reference'
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        
        payload = {
            "amount": int(amount),
            "email": email,
            "reference": reference,
        }
        
        if metadata:
            payload["metadata"] = metadata
            
        if callback_url:
            payload["callback_url"] = callback_url
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            # Log raw response for debugging if needed
            # logger.debug(f"Paystack response: {response.text}")
            
            if response.status_code >= 400:
                return {"status": False, "message": response.text}
                
            data = response.json()
            
            if data.get("status"):
                return {
                    "status": True,
                    "authorization_url": data["data"]["authorization_url"],
                    "access_code": data["data"]["access_code"],
                    "reference": data["data"]["reference"],
                }
            else:
                logger.error(f"Paystack init failed: {data.get('message')}")
                return {"status": False, "message": data.get('message')}
                
        except requests.RequestException as e:
            logger.exception(f"Paystack API error: {str(e)}")
            return {"status": False, "message": str(e)}
    


def verify_transaction(self, reference: str) -> Dict:
    """
    Verify a transaction status.
    
    Args:
        reference: Transaction reference to verify
        
    Returns:
        Dict with transaction details
    """
    # Clean and safely encode the user-controlled reference 
    # to block path traversal attacks (e.g., converting '/' to '%2F')
    safe_reference = quote(str(reference), safe='')
    
    url = f"{self.BASE_URL}/transaction/verify/{safe_reference}"
    
    try:
        response = requests.get(url, headers=self.headers)
        if response.status_code >= 400:
            return {"status": False, "message": response.text}
            
        data = response.json()
        
        if data.get("status"):
            transaction_data = data["data"]
            return {
                "status": True,
                "reference": transaction_data["reference"],
                "amount": transaction_data["amount"],
                "paid_at": transaction_data.get("paid_at"),
                "channel": transaction_data.get("channel"),
                "transaction_status": transaction_data["status"],  # 'success', 'failed', 'abandoned'
                "customer": transaction_data.get("customer"),
                "metadata": transaction_data.get("metadata"),
            }
        else:
            return {"status": False, "message": data.get("message")}
            
    except requests.RequestException as e:
        logger.exception(f"Paystack verify error: {str(e)}")
        return {"status": False, "message": str(e)}

    
def validate_webhook(self, signature: str, payload: bytes) -> bool:
    """
    Validate webhook signature from Paystack.
    
    Args:
        signature: X-Paystack-Signature header value
        payload: Raw request body (bytes)
        
    Returns:
        True if signature is valid
    """
    if not signature:
        return False
        
    hash_object = hmac.new(
        self.secret_key.encode('utf-8'),
        payload,
        hashlib.sha512
    )
    expected_signature = hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
