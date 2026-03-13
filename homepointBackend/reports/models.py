from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

User = get_user_model()


class Report(models.Model):
    """
    Base model for storing generated reports
    """
    REPORT_TYPES = [
        ('DAILY_SALES', 'Daily Sales Summary'),
        ('PERIOD_SALES', 'Period Sales Report'),
        ('PAYMENT_METHOD', 'Payment Method Breakdown'),
        ('CASH_FLOW', 'Cash Flow Statement'),
        ('MPESA_RECONCILIATION', 'M-Pesa Reconciliation'),
        ('ACCOUNT_LEDGER', 'Account Ledger'),
        ('USER_PERFORMANCE', 'User Performance Report'),
        ('PRODUCT_SALES', 'Product Sales Analysis'),
        ('TAX_REPORT', 'Tax Report (VAT)'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Report metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Report data - stored as JSON for flexibility
    data = models.JSONField(default=dict)
    
    # Summary metrics (denormalized for quick access)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    
    # File storage (if generating PDF/Excel)
    file = models.FileField(upload_to='reports/%Y/%m/', blank=True, null=True)
    
    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', '-generated_at']),
            models.Index(fields=['generated_by', '-generated_at']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date.date()}"


class DailySalesSnapshot(models.Model):
    """
    Daily summary snapshots for quick historical access
    Pre-aggregated data for performance
    """
    date = models.DateField(unique=True, db_index=True)
    
    # Sales metrics
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    
    # Payment breakdown
    mpesa_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mpesa_count = models.IntegerField(default=0)
    cash_count = models.IntegerField(default=0)
    
    # Tax
    total_vat = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Account balances at end of day
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    mpesa_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Metadata
    snapshot_created_at = models.DateTimeField(auto_now_add=True)
    snapshot_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Daily Sales Snapshot'
        verbose_name_plural = 'Daily Sales Snapshots'
    
    def __str__(self):
        return f"Sales Snapshot - {self.date}"


class ReportSchedule(models.Model):
    """
    Automated report generation schedule
    """
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]
    
    report_type = models.CharField(max_length=30, choices=Report.REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='scheduled_reports')
    
    # Email settings
    send_email = models.BooleanField(default=True)
    email_subject_template = models.CharField(max_length=255, blank=True)
    
    # Schedule
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.get_frequency_display()}"


class AccountReconciliation(models.Model):
    """
    Track account reconciliation activities
    Important for M-Pesa and Bank account matching
    """
    RECONCILIATION_TYPES = [
        ('MPESA', 'M-Pesa Reconciliation'),
        ('BANK', 'Bank Reconciliation'),
        ('CASH', 'Cash Count Reconciliation'),
    ]
    
    STATUS_CHOICES = [
        ('MATCHED', 'Matched'),
        ('DISCREPANCY', 'Discrepancy Found'),
        ('PENDING', 'Pending Review'),
        ('RESOLVED', 'Resolved'),
    ]
    
    reconciliation_type = models.CharField(max_length=20, choices=RECONCILIATION_TYPES)
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='reconciliations')
    
    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Expected vs Actual
    expected_balance = models.DecimalField(max_digits=15, decimal_places=2)
    actual_balance = models.DecimalField(max_digits=15, decimal_places=2)
    variance = models.DecimalField(max_digits=15, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)
    
    # Details stored as JSON
    details = models.JSONField(default=dict, blank=True)
    
    # Tracking
    reconciled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reconciled_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-reconciled_at']
        indexes = [
            models.Index(fields=['account', '-reconciled_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_reconciliation_type_display()} - {self.start_date.date()}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate variance
        self.variance = self.actual_balance - self.expected_balance
        
        # Auto-set status based on variance
        if self.variance == Decimal('0'):
            self.status = 'MATCHED'
        elif self.status == 'PENDING':
            self.status = 'DISCREPANCY'
        
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """
    Audit trail for financial transactions
    Immutable record of all financial operations
    """
    ACTION_TYPES = [
        ('TRANSACTION_CREATED', 'Transaction Created'),
        ('TRANSACTION_MODIFIED', 'Transaction Modified'),
        ('PAYMENT_COMPLETED', 'Payment Completed'),
        ('PAYMENT_REFUNDED', 'Payment Refunded'),
        ('ACCOUNT_ADJUSTED', 'Account Balance Adjusted'),
        ('REPORT_GENERATED', 'Report Generated'),
        ('RECONCILIATION_PERFORMED', 'Reconciliation Performed'),
    ]
    
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    
    # What was affected
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    
    # Changes
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    
    # Context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.timestamp}"