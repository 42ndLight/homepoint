# payments/views.py
from rest_framework import generics, status
from django.db import transaction
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from products.permissions import IsWarehouseStaff
from rest_framework.response import Response
from .serializers import (
    TransactionHistorySerializer,
    MpesaCheckoutSerializer,
    CashRecordSerializer
)
from .models import Transaction, MpesaTransaction, CashTransaction


class TransactionHistoryListView(generics.ListAPIView):
    serializer_class = TransactionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)


class MpesaCheckoutCreateView(generics.CreateAPIView):
    serializer_class = MpesaCheckoutSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        #mpesa_tx = serializer.save(status='PENDING')
        # Here: call daraja STK push service
        # Example: result = initiate_stk_push(mpesa_tx)
        # Then update checkout_request_id etc.
        # If fails → raise ValidationError
        data = serializer.validated_data
        amount = data['amount']
        

        


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

        if t_type == 'SALES':
            if amount < order.total_amount:
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