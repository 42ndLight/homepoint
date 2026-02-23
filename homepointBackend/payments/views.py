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
            return Transaction.objects.all()
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
    try:
        data = json.loads(raw)
    except Exception:
        data = request.POST.dict() if request.POST else raw

    # MPesa often nests payload under Body / stkCallback etc. Normalize for easier inspection.
    payload = data.get('Body', data) if isinstance(data, dict) else data
    print("M-Pesa Confirmation parsed payload:", payload)

    # to do: integrate with models (use transaction_id / BillRefNumber etc.)
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
    # return JsonResponse({
    #     "ResultCode": 0,
    #     "ResultDesc": "Success"
    # })

@csrf_exempt
@api_view(['POST'])
def mpesa_validation(request):
    if request.method == 'POST':        
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })
    return JsonResponse({"error": "Invalid request"}, status=400)






