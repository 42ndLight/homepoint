from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
from ..paystack.client import PaystackClient
from ..models import PaystackTransaction, Account
from ..serializers import PaystackInitializeSerializer
import uuid
import re
import logging

logger = logging.getLogger(__name__)

class PaystackInitializeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PaystackInitializeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = serializer.validated_data['order']
        email = serializer.validated_data['email']
        
        # Paystack amount is in kobo (shillings * 100)
        amount = int(order.total_amount * 100)
        reference = f"HP-{order.id}-{uuid.uuid4().hex[:8]}"
        
        # Use backend endpoint as callback_url
        callback_url = request.build_absolute_uri(
            reverse('payments:paystack-callback')
        )
        
        client = PaystackClient()
        response = client.initialize_transaction(
            amount=amount,
            email=email,
            reference=reference,
            callback_url=callback_url,
            metadata={"order_id": order.id, "user_id": request.user.id}
        )
        
        if response['status']:
            # Create a pending transaction record
            with transaction.atomic():
                PaystackTransaction.objects.create(
                    user=request.user,
                    order=order,
                    amount=order.total_amount,
                    movement_type='IN',
                    transaction_type='SALES',
                    status='PENDING',
                    paystack_reference=reference,
                    customer_email=email,
                    access_code=response['access_code'],
                    balance_after=0 # Will be updated on success
                )
                
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": response.get('message', 'Failed to initialize transaction')},
                status=status.HTTP_400_BAD_REQUEST
            )

class PaystackCallbackView(APIView):
    """
    Handle the user redirect back from Paystack.
    This performs verification and then redirects to the frontend.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        reference = request.GET.get('reference')
        
        # 1. Reject missing references immediately
        if not reference:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
            if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS:
                frontend_url = settings.CORS_ALLOWED_ORIGINS[0]
            return redirect(f"{frontend_url}/pos")
            
        # 2. Strict Alphanumeric + Hyphen validation to block path traversal early        
        if not re.match(r'^[a-zA-Z0-9\-_]+$', reference):
            logger.warning(f"Malicious reference format blocked: {reference}")
            frontend_url = getattr(settings, 'FRONTEND_URL')
            if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS:
                frontend_url = settings.CORS_ALLOWED_ORIGINS[0]
            return redirect(f"{frontend_url}/pos")

        client = PaystackClient()
        response = client.verify_transaction(reference)
        
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        # If CORS_ALLOWED_ORIGINS is set, use the first one as default frontend
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS:
             frontend_url = settings.CORS_ALLOWED_ORIGINS[0]

        if response['status'] and response['transaction_status'] == 'success':
            from ..services import confirm_paystack_payment
            confirm_paystack_payment(reference, response)
            
        return redirect(f"{frontend_url}/pos")

class PaystackVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        # Find the latest paystack transaction for this order
        tx = get_object_or_404(
            PaystackTransaction.objects.filter(order_id=order_id).order_by('-timestamp')[:1]
        )
        reference = tx.paystack_reference
        
        client = PaystackClient()
        response = client.verify_transaction(reference)
        
        if response['status']:
            if response['transaction_status'] == 'success' and tx.status != 'SUCCESS':
                from ..services import confirm_paystack_payment
                confirm_paystack_payment(reference, response)
                
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": response.get('message', 'Failed to verify transaction')},
                status=status.HTTP_400_BAD_REQUEST
            )
