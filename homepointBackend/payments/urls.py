from .views import MpesaCheckoutCreateView, CashTransactionCreateView, TransactionHistoryListView
from django.urls import path

app_name = 'payments'

urlpatterns = [
    path('transactions/', TransactionHistoryListView.as_view(), name='transaction-history'),
    path('mpesa/checkout/', MpesaCheckoutCreateView.as_view(), name='mpesa-checkout'),
    path('cash/', CashTransactionCreateView.as_view(), name='cash-transaction'),
]