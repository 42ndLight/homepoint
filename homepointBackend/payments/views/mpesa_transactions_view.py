#mpesa_transactions_view.py

from rest_framework import generics, status, serializers
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from payments.utils import get_mpesa_access_token
from products.permissions import IsWarehouseStaff
from rest_framework.response import Response
from payments.serializers import MpesaCheckoutSerializer    
from payments.models import MpesaTransaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json



@csrf_exempt
@api_view(['POST'])
def mpesa_confirmation_url(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request"}, status=400)

    # Log headers and raw body for debugging (replace print with logging in production)
    raw = request.body.decode('utf-8', errors='replace') if request.body else ''
    print("M-Pesa Confirmation headers:", dict(request.headers))
    print("M-Pesa Confirmation raw body:", raw)

    # Try to parse JSON, fallback to form data or raw string
    data = json.loads(raw)

    trans_id = data.get('TransID')
    bill_ref = data.get('BillRefNumber')
    amount = data.get('TransAmount')
    phone = data.get('MSISDN')
    org_bal = data.get('OrgAccountBalance')

    #order_id = ''.join(filter(str.isdigit, bill_ref)) if bill_ref else None
    try:
        with transaction.atomic():
            order = Order.objects.get(id=order_id)

            mpesa_tx, created = MpesaTransaction.objects.update_or_create(
                mpesa_receipt_number=trans_id,
                defaults={
                    'order': order,
                    'user': order.user, # Linking to the user who made the order
                    'amount': amount,
                    'movement_type': 'IN',
                    'transaction_type': 'SALES',
                    'phone_number': phone,
                    'status': 'SUCCESS',
                    'callback_data': data,
                    'reference_id': trans_id,
                    'balance_after': org_bal, # In a real ledger, calculate based on Account balance
                }
            )

            # Update Order Status
            if order.status != 'paid':
                order.status = 'paid'
                order.save(update_fields=['status'])
            
            # Update the M-Pesa Account balance if you have one defined
            mpesa_account = Account.objects.filter(account_type='MPESA').first()
            if mpesa_account:
                mpesa_account.balance += float(amount)
                mpesa_account.save()

    # to do: integrate with models (use transaction_id / BillRefNumber etc.)
            
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})

    except Order.DoesNotExist:
        print(f"Order {order_id} not found for M-Pesa Trans {trans_id}")
        # Even if order isn't found, we often return Success to M-Pesa to stop retries,
        # but log it for manual reconciliation.
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Order not found"})
    except Exception as e:
        print(f"Error processing M-Pesa confirmation: {str(e)}")
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Internal Error"}, status=500)

@csrf_exempt
@api_view(['POST'])
def mpesa_validation(request):
    if request.method == 'POST':        
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })
    return JsonResponse({"error": "Invalid request"}, status=400)


