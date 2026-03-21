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
         


from rest_framework import generics, serializers
from .services import record_cash_sale, record_expense, record_deposit, record_withdrawal
from django.db import transaction as db_transaction

class CashTransactionCreateView(generics.ListCreateAPIView):
    serializer_class = CashRecordSerializer
    permission_classes = [IsAuthenticated, IsWarehouseStaff]
    queryset = CashTransaction.objects.all()

    def perform_create(self, serializer):
        data = serializer.validated_data
        t_type = data.get('transaction_type')
        user = self.request.user
        amount = data.get('amount')
        
        # Use a mapping or if/elif to call the specific service
        try:
            if t_type == 'SALES' or t_type == 'SALE':
                if not data.get('order'):
                    raise serializers.ValidationError({"order_id": "Order is required for sales."})
                
                record_cash_sale(
                    user=user,
                    order=data['order'],
                    amount=amount,
                    receipt_number=data.get('receipt_number', ''),
                    notes=data.get('notes', '')
                )

            elif t_type == 'EXPENSE':
                # Note: Expense might need a 'category' from request data 
                # If not in serializer, provide a default or update serializer
                record_expense(
                    user=user,
                    amount=amount,
                    category=data.get('category', 'OTHER'), 
                    source_account_type='CASH',
                    supplier=data.get('supplier', ''),
                    notes=data.get('notes', '')
                )

            elif t_type == 'DEPOSIT':
                # Records moving cash OUT of 'CASH' account into 'BANK'
                record_deposit(
                    user=user,
                    amount=amount,
                    authorized_by=user, # Or specific logic for authorizer
                    source_account_type='CASH',
                    dest_account_type='BANK',
                    notes=data.get('notes', '')
                )

            elif t_type == 'WITHDRAWAL':
                # Records moving money from 'BANK' into 'CASH'
                record_withdrawal(
                    user=user,
                    amount=amount,
                    authorized_by=user,
                    source_account_type='BANK',
                    notes=data.get('notes', '')
                )
            
            else:
                raise serializers.ValidationError(f"Unsupported transaction type: {t_type}")

        except ValueError as e:
            # Catch 'Insufficient balance' errors from services
            raise serializers.ValidationError({"detail": str(e)})



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






