# payments/views.py
from rest_framework import generics, status
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .utils import get_mpesa_access_token
from products.permissions import IsWarehouseStaff
from rest_framework.response import Response
from .serializers import (
    TransactionHistorySerializer,
    MpesaCheckoutSerializer,
    CashRecordSerializer
)
from .models import Transaction, MpesaTransaction, CashTransaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


class TransactionHistoryListView(generics.ListAPIView):
    serializer_class = TransactionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.select_subclasses().all()
        return Transaction.objects.filter(user=self.request.user)
         


class CashTransactionCreateView(generics.ListCreateAPIView):
    serializer_class = CashRecordSerializer
    permission_classes = [IsAuthenticated, IsWarehouseStaff]

    queryset = CashTransaction.objects.all()

    @transaction.atomic
    def perform_create(self, serializer):
        data = serializer.validated_data
        amount = data['amount']
        t_type = data['transaction_type']
        order = data.get('order')
        user = self.request.user

        if t_type == 'SALES' and amount < order.total_amount:

            raise serializers.ValidationError("Amount must cover the order total.")

              # Create main transaction record
        tx = Transaction.objects.create(
            user=user,
            movement_type='IN' if t_type == 'SALES' else 'OUT',
            transaction_type=t_type if order else 'OTHER',
            amount=amount if t_type == 'SALES' else -amount,
            balance_after=0,
            reference_id=data.get('reference_id', ''),
            notes=data.get('notes', '')
        )

        CashTransaction.objects.create(
            transaction=tx,
            amount=amount,
            order=order,
            recorded_by=self.request.user
        )

        # If paying an order → update order status
        if order and t_type == 'SALES':
            order.status = 'paid'
            order.save(update_fields=['status'])



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

    order_id = ''.join(filter(str.isdigit, bill_ref)) if bill_ref else None
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






