from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from ..paystack.client import PaystackClient
from ..services import confirm_paystack_payment
import logging

logger = logging.getLogger(__name__)

class PaystackWebhookView(APIView):
    permission_classes = [] # Public endpoint, signature is verified

    def post(self, request):
        signature = request.headers.get('x-paystack-signature')
        payload = request.body
        
        client = PaystackClient()
        if not client.validate_webhook(signature, payload):
            logger.warning("Invalid Paystack webhook signature")
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
            
        data = request.data
        event = data.get('event')
        
        if event == 'charge.success':
            reference = data['data']['reference']
            try:
                confirm_paystack_payment(reference, data)
                logger.info(f"Paystack payment successful for reference: {reference}")
            except Exception as e:
                logger.error(f"Error processing Paystack webhook: {str(e)}")
                return Response({"error": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response({"status": "received"}, status=status.HTTP_200_OK)
