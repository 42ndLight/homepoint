from .views import mpesa_confirmation_url, mpesa_validation, CashTransactionCreateView, TransactionHistoryListView
from django.urls import path

app_name = 'payments'

urlpatterns = [
    path('transactions/', TransactionHistoryListView.as_view(), name='transaction-history'),
    path('cash/', CashTransactionCreateView.as_view(), name='cash-transaction'),
    path('confirmation/', mpesa_confirmation_url, name='mpesa-confirmation'),
    path('validation/', mpesa_validation, name='mpesa-validation'),
]