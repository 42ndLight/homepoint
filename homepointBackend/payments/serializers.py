from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import (
    Transaction, MpesaTransaction, CashTransaction, Account,
    SaleTransaction, ExpenseTransaction, DepositWithdrawal
)
from orders.models import Order  # assuming you have this


class TransactionHistorySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for complete transaction history
    Perfect for user dashboard + admin audit + eTIMS export
    """
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(source='order', read_only=True)
    order_number = serializers.CharField(source='order.id', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'movement_type', 'movement_type_display',
            'transaction_type', 'transaction_type_display',
            'amount', 'balance_after',
            'timestamp', 'reference_id', 'notes',
            'order_id', 'order_number', 'order_status', 'status',
        ]
        read_only_fields = fields  # enforce read-only

    def get_status(self, obj):
        # Return status if it exists on subclass (e.g. MpesaTransaction)
        return getattr(obj, 'status', None)


class MpesaCheckoutSerializer(serializers.ModelSerializer):
    """
    Input serializer to initiate STK Push
    Used by frontend → POST to trigger payment
    """
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.filter(status='pending'),
        write_only=True,
        source='order'
    )
    order_total_amount = serializers.DecimalField(
        source='order.total_amount',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    phone_number = serializers.CharField(max_length=15, required=True)    
    reference_id = serializers.CharField(max_length=100, required=False, write_only=True)
    

    class Meta:
        model = MpesaTransaction
        fields = ['phone_number', 'order_id', 'order_total_amount', 'reference_id']

    def validate(self, data):
        order = data['order']
        if order.total_amount <= 0:
            raise serializers.ValidationError("Order has no amount to pay.")
        if order.status != 'pending':
            raise serializers.ValidationError("Order is not in pending state.")
        return data


class CashRecordSerializer(serializers.ModelSerializer):
    """
    Admin / staff only – record manual cash payment / deposit / withdrawal
    """
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        required=False,
        source='order'
    )
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    transaction_type = serializers.ChoiceField(choices=Transaction.TYPE_CHOICES, write_only=True)
    
    reference_id = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)
    
    # Extra fields for specific transaction types (handled in view/service)
    category = serializers.CharField(max_length=20, required=False, allow_blank=True, write_only=True)
    supplier = serializers.CharField(max_length=100, required=False, allow_blank=True, write_only=True)

    class Meta:
        model = CashTransaction
        fields = [
            'amount', 'order_id', 'transaction_type', 
            'reference_id', 'receipt_number', 'notes',
            'recorded_by', 'created_at',
            'category', 'supplier',
        ]
        read_only_fields = ['recorded_by', 'created_at']


    def validate(self, data):
        # Your custom logic: Check if Sale amount matches Order total
        order = data.get('order')
        amount = data.get('amount')
        t_type = data.get('transaction_type')

        if t_type == 'SALE' and order and amount < order.total_amount:
            raise serializers.ValidationError(f"Amount {amount} is less than Order total {order.total_amount}")

        return data   

    def create(self, validated_data):
        # This is usually wrapped in a view/service with @transaction.atomic
        # Here we just prepare data – real creation happens in view

        return validated_data


'''class SaleTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleTransaction
        fields = [
            'id', 'account', 'user', 'movement_type', 'transaction_type',
            'amount', 'balance_after', 'timestamp', 'reference_id', 'notes',
            'order', 'payment_method'
        ]
        read_only_fields = ['balance_after', 'timestamp']

class ExpenseTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseTransaction
        fields = [
            'id', 'account', 'user', 'movement_type', 'transaction_type',
            'amount', 'balance_after', 'timestamp', 'reference_id', 'notes',
            'category', 'supplier', 'approved_by'
        ]
        read_only_fields = ['balance_after', 'timestamp']

class DepositTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositWithdrawal
        fields = [
            'id', 'account', 'user', 'movement_type', 'transaction_type',
            'amount', 'balance_after', 'timestamp', 'reference_id', 'notes',
            'destination_account', 'authorized_by'
        ]
        read_only_fields = ['balance_after', 'timestamp']

class WithdrawalTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositWithdrawal
        fields = [
            'id', 'account', 'user', 'movement_type', 'transaction_type',
            'amount', 'balance_after', 'timestamp', 'reference_id', 'notes',
            'destination_account', 'authorized_by'
        ]
        read_only_fields = ['balance_after', 'timestamp']'''