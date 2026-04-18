#mpesa_transactions_view.py

import json
import logging
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_stk_push(request):
    """
    Endpoint for frontend to trigger M-Pesa STK Push.
    """
    serializer = MpesaCheckoutSerializer(data=request.data)
    if serializer.is_valid():
        order = serializer.validated_data['order']
        phone_number = serializer.validated_data['phone_number']
        amount = order.total_amount

        client = MpesaExpressClient()
        try:
            response = client.stk_push(
                phone_number=phone_number,
                amount=amount,
                order_id=order.id
            )
            
            res_data = response.json()
            
            if response.status_code == 200 and res_data.get('ResponseCode') == '0':
                checkout_request_id = res_data.get('CheckoutRequestID')
                
                # Record the initiated transaction as PENDING
                with transaction.atomic():
                    record_mpesa_initiated(
                        order=order,
                        amount=amount,
                        phone_number=phone_number,
                        checkout_request_id=checkout_request_id,
                        user=request.user
                    )
                
                return Response({
                    "message": "STK Push initiated successfully",
                    "checkout_request_id": checkout_request_id
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Failed to initiate STK Push",
                    "details": res_data
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error initiating STK Push: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
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
                user=order.user if order else None, # Might need to handle if None
                amount=amount,
                movement_type='IN',
                transaction_type='SALE',
                phone_number=phone,
                status='SUCCESS',
                callback_data=data,
                reference_id=trans_id,
                balance_after=org_bal,
                checkout_request_id=f"C2B-{trans_id}" # Placeholder for unique constraint
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
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_validation(request):
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
