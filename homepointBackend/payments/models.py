from django.db import models
from orders.models import Order, User
from django.conf import settings


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('CASH', 'Cash Office'),
        ('MPESA', 'M-Pesa Paybill'),
        ('BANK', 'Bank Account'),
        ('REVENUE', 'Sales Revenue'), # Virtual account for COGS/Sales
        ('EXPENSE', 'Expenses/Purchases'),
    ]
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.account_type})"

class Transaction(models.Model):      
    TYPE_CHOICES = [
        ('SALES', 'Sales Payment'),
        ('DEPOSIT', 'Cash Deposit'),
        ('WITHDRAWAL', 'Cash Withdrawal'),
        ('REFUND', 'Refund'),
        ('EXPENSE', 'Expense Payment'),
        ('PURCHASE', 'Purchase Payment'),
    ]
    MOVEMENT_CHOICES = [('IN', 'Money In'), ('OUT', 'Money Out')]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='ledger', default=None, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SALES')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2) # Crucial for audits
    timestamp = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=100, blank=True, db_index=True,
                                    help_text="M-Pesa Receipt, Cash Receipt No, etc.")
    notes = models.TextField(blank=True)


    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.movement_type} - {self.amount} ({self.user.username})"




class MpesaTransaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='mpesa_transactions', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='mpesa_transactions')
    checkout_request_id = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_date = models.DateTimeField(auto_now_add=True)
    callback_data = models.JSONField(blank=True, null=True)  # Store full callback response

    class Meta:
        indexes = [models.Index(fields=['checkout_request_id']), models.Index(fields=['mpesa_receipt_number'])]

    def __str__(self):
        return f"M-Pesa {self.status} – Order #{self.order_id} – {self.phone_number}"

class CashTransaction(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='cash_transactions', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='cash_transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='recorded_cash_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Cash {self.transaction.movement_type} – {self.transaction.amount}"