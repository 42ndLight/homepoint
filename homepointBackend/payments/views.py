# payments/views.py
from rest_framework import generics, status
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .utils import get_mpesa_access_token, register_mpesa_urls
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


class MpesaCheckoutCreateView(APIView):
    
    permission_classes = [AllowAny]

           

    def post(self, request):
        #mpesa_tx = serializer.save(status='PENDING')
        # Here: call daraja STK push service
        # Example: result = initiate_stk_push(mpesa_tx)
        # Then update checkout_request_id etc.
        # If fails → raise ValidationError
        
        response = register_mpesa_urls()
        if response.status_code == 200:
            return Response({"message": response.json()}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to register M-Pesa URLs.", "details": response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        

        


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

class MpesaAuthView(APIView):

    def get(self, request):
        try:
            access_token = get_mpesa_access_token()
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def mpesa_confirmation_url(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Extract key fields for HomePoint processing
            '''transaction_id = data.get('TransID')
            amount = data.get('TransAmount')
            bill_ref = data.get('BillRefNumber')  # Use this for order ID or customer ref
            phone = data.get('MSISDN')  # Hashed phone number
            first_name = data.get('FirstName')'''
            # TODO: Integrate with your models
            # e.g., Order.objects.filter(id=bill_ref).update(paid=True, payment_method='M-Pesa')
            # Or save to a Transaction model for inventory tracking
            # from .models import Transaction
            # Transaction.objects.create(
            #     transaction_id=transaction_id,
            #     amount=amount,
            #     bill_ref=bill_ref,
            #     phone=phone,
            #     first_name=first_name
            # )
            print("M-Pesa Confirmation:", data)  # Log for dev; replace with logging
            return JsonResponse({
                "ResultCode": 0,
                "ResultDesc": "Success"
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def mpesa_validation(request):
    if request.method == 'POST':
        # Optional: Add logic to validate (e.g., check if account exists)
        # For MVP, always accept
        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })
    return JsonResponse({"error": "Invalid request"}, status=400)

    


    
