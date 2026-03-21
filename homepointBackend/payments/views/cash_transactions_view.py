#cash_transactions_view.py
from rest_framework import generics, serializers
from payments.serializers import CashRecordSerializer
from rest_framework.permissions import IsAuthenticated
from payments.models import CashTransaction
from payments.services import record_cash_sale, record_expense, record_deposit, record_withdrawal
from django.db import transaction as db_transaction

from payments.utils import get_mpesa_access_token
from products.permissions import IsWarehouseStaff
from payments.serializers import CashRecordSerializer


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
