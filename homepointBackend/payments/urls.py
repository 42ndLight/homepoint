from django.urls import path
from payments.views.mpesa_transactions_view import (
    mpesa_confirmation_url, 
    mpesa_validation,
    initiate_stk_push,
    stk_callback,
    check_order_payment_status
)
from payments.views.cash_transactions_view import CashTransactionCreateView
from payments.views.transactions_views import TransactionHistoryListView

from payments.views.paystack_transactions_view import PaystackInitializeView, PaystackVerifyView, PaystackCallbackView
from payments.views.paystack_webhook_view import PaystackWebhookView

app_name = 'payments'

urlpatterns = [
    path('transactions/', TransactionHistoryListView.as_view(), name='transaction-history'),
    path('cash/', CashTransactionCreateView.as_view(), name='cash-transaction'),
    
    # M-Pesa C2B
    path('confirmation/', mpesa_confirmation_url, name='mpesa-confirmation'),
    path('validation/', mpesa_validation, name='mpesa-validation'),
    
    # M-Pesa Express (STK Push)
    path('initiate-stk-push/', initiate_stk_push, name='initiate-stk-push'),
    path('stk-callback/', stk_callback, name='stk-callback'),
    path('check-status/<int:order_id>/', check_order_payment_status, name='check-payment-status'),

    # Paystack
    path('paystack/initialize/', PaystackInitializeView.as_view(), name='paystack-initialize'),
    path('paystack/verify/<int:order_id>/', PaystackVerifyView.as_view(), name='paystack-verify'),
    path('paystack/callback/', PaystackCallbackView.as_view(), name='paystack-callback'),
    path('paystack/webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]
