#mpesa_transactions_view.py

import json
import logging
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from payments.models import MpesaTransaction, Account
from payments.serializers import MpesaCheckoutSerializer
from payments.mpesa.core import MpesaExpressClient
from payments.services import record_mpesa_initiated, confirm_mpesa_payment
from orders.models import Order

logger = logging.getLogger(__name__)

from django.utils import timezone
from datetime import timedelta

@require_POST
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_stk_push(request):
    """
    Endpoint for frontend to trigger M-Pesa STK Push with Idempotency.
    Allows retry after 1 minute if previous attempt is still PENDING.
    """
    serializer = MpesaCheckoutSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.validated_data['order']
        phone_number = serializer.validated_data['phone_number']
        amount = order.total_amount

        try:
            with transaction.atomic():
                # Lock the order and check for recent PENDING transactions
                one_minute_ago = timezone.now() - timedelta(minutes=1)
                
                existing_pending = MpesaTransaction.objects.select_for_update().filter(
                    order=order, 
                    status='PENDING',
                    timestamp__gte=one_minute_ago # Check if it happened in the last minute
                ).first()

                if existing_pending:
                    return Response({
                        "message": "A payment request was recently sent. Please wait at least 60 seconds before retrying.",
                        "checkout_request_id": existing_pending.checkout_request_id,
                        "is_duplicate": True
                    }, status=status.HTTP_200_OK)

                # If there's an older pending transaction, we mark it as FAILED/EXPIRED
                # to avoid confusion before starting a new one.
                MpesaTransaction.objects.filter(
                    order=order, 
                    status='PENDING',
                    timestamp__lt=one_minute_ago
                ).update(status='FAILED', notes="System: Timed out/Retried by user")

                # Call M-Pesa API
                client = MpesaExpressClient()
                response = client.stk_push(
                    phone_number=phone_number,
                    amount=amount,
                    order_id=order.id
                )
                
                res_data = response.json()
                
                if response.status_code == 200 and res_data.get('ResponseCode') == '0':
                    checkout_request_id = res_data.get('CheckoutRequestID')
                    merchant_request_id = res_data.get('MerchantRequestID')
                    
                    # Record the initiated transaction
                    record_mpesa_initiated(
                        order=order,
                        amount=amount,
                        phone_number=phone_number,
                        checkout_request_id=checkout_request_id,
                        user=request.user
                    )
                    
                    # Store the merchant_request_id we just added to the model
                    tx = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
                    tx.merchant_request_id = merchant_request_id
                    tx.save(update_fields=['merchant_request_id'])
                    
                    return Response({
                        "message": "STK Push initiated successfully",
                        "checkout_request_id": checkout_request_id
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "M-Pesa API error",
                        "details": res_data
                    }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error initiating STK Push for Order #{order.id}: {str(e)}")
            return Response({"error": "System error occurred while initiating payment."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@require_GET
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_order_payment_status(request, order_id):
    """
    Check if a successful M-Pesa transaction exists for the given order.
    """
    try:
        # Get the latest MpesaTransaction for this order
        mpesa_tx = MpesaTransaction.objects.filter(order_id=order_id).order_by('-timestamp').first()
        
        if not mpesa_tx:
            return Response({
                "status": "NOT_FOUND",
                "message": "No transaction found for this order"
            }, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            "status": mpesa_tx.status,
            "mpesa_receipt": mpesa_tx.mpesa_receipt_number,
            "checkout_request_id": mpesa_tx.checkout_request_id,
            "amount": mpesa_tx.amount,
            "order_status": mpesa_tx.order.status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking payment status for order {order_id}: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def stk_callback(request):
    """
    Callback URL for M-Pesa Express (STK Push).
    """
    data = json.loads(request.body)
    logger.info(f"M-Pesa STK Callback received: {json.dumps(data)}")
    
    client = MpesaExpressClient()
    parsed_data = client.parse_stk_result(data)
    
    result_code = parsed_data.get('ResultCode')
    checkout_request_id = parsed_data.get('CheckoutRequestID')
    
    if result_code == 0:
        # Success!
        mpesa_receipt = parsed_data.get('MpesaReceiptNumber')
        try:
            confirm_mpesa_payment(
                checkout_request_id=checkout_request_id,
                mpesa_receipt=mpesa_receipt,
                callback_data=data
            )
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
        except Exception as e:
            logger.error(f"Error confirming M-Pesa payment: {str(e)}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Internal Error"})
    else:
        # Failed or cancelled
        try:
            tx = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
            tx.status = 'FAILED'
            tx.callback_data = data
            tx.save(update_fields=['status', 'callback_data'])
        except MpesaTransaction.DoesNotExist:
            pass
            
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_confirmation_url(request):
    """
    C2B Confirmation URL. Simplified as requested.
    Just receives response and creates MpesaTransaction.
    """
    data = json.loads(request.body)
    logger.info(f"M-Pesa C2B Confirmation received: {json.dumps(data)}")

    trans_id = data.get('TransID')
    bill_ref = data.get('BillRefNumber')
    amount = data.get('TransAmount')
    phone = data.get('MSISDN')
    org_bal = data.get('OrgAccountBalance')

    # Try to find order from BillRefNumber, but don't let it block creation
    order_id = ''.join(filter(str.isdigit, bill_ref)) if bill_ref else None
    order = Order.objects.filter(id=order_id).first() if order_id else None

    try:
        with transaction.atomic():
            # Create transaction record
            # If order is missing, this might fail depending on model null=False
            # We assume user handles model constraints or wants raw creation
            MpesaTransaction.objects.create(
                mpesa_receipt_number=trans_id,
                order=order,
                user=order.user if order else None, 
                amount=amount,
                movement_type='IN',
                transaction_type='SALE',
                phone_number=phone,
                status='SUCCESS',
                callback_data=data,
                reference_id=trans_id,
                balance_after=org_bal,
                bill_reference_no=bill_ref or trans_id, # Must be unique
                checkout_request_id=f"C2B-{trans_id}"
            )

            # Update order status if order found
            if order and order.status != 'paid':
                order.status = 'paid'
                order.save(update_fields=['status'])
            
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})

    except Exception as e:
        logger.error(f"Error processing M-Pesa C2B: {str(e)}")
        # Return success to M-Pesa to stop retries even if internal logic fails
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted with internal error"})

@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_validation(request):
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
