from .views import mpesa_confirmation_url, mpesa_validation,MpesaCheckoutCreateView, CashTransactionCreateView, TransactionHistoryListView, MpesaAuthView
from django.urls import path

app_name = 'payments'

urlpatterns = [
    path('transactions/', TransactionHistoryListView.as_view(), name='transaction-history'),
    path('mpesa/checkout/', MpesaCheckoutCreateView.as_view(), name='mpesa-checkout'),
    path('cash/', CashTransactionCreateView.as_view(), name='cash-transaction'),
    path('mpesa/auth/', MpesaAuthView.as_view(), name='mpesa-auth'),
    path('confirmation/', mpesa_confirmation_url, name='mpesa-confirmation'),
    path('validation/', mpesa_validation, name='mpesa-validation'),
]