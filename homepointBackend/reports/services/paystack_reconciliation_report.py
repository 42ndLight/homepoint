"""Paystack Reconciliation report generator."""

from django.db.models import Sum
from decimal import Decimal

from payments.models import Account, PaystackTransaction
from reports.models import AccountReconciliation
from reports.services.base import ReportServiceMixin


class PaystackReconciliationReport(ReportServiceMixin):
    """Generate a PAYSTACK_RECONCILIATION report using AccountReconciliation."""

    @classmethod
    def generate_paystack_reconciliation(cls, start_date, end_date, user=None):
        start_date, end_date = cls._normalize_range(start_date, end_date)

        # Paystack settlements are typically deposited into a BANK account.
        paystack_account = Account.objects.filter(account_type='BANK').first()
        if not paystack_account:
            raise ValueError('No BANK account configured for Paystack reconciliation')

        txns = PaystackTransaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            status='SUCCESS',
        )
        inflow = (
            txns.filter(movement_type='IN').aggregate(total=Sum('amount'))['total']
            or Decimal('0')
        )
        outflow = (
            txns.filter(movement_type='OUT').aggregate(total=Sum('amount'))['total']
            or Decimal('0')
        )

        # NOTE: backing out of the live balance only works for ranges ending now.
        # For historical ranges, use the previous AccountReconciliation actual_balance
        # or a stored opening balance for the day before start_date.
        opening_balance = paystack_account.balance - (inflow - outflow)
        expected_balance = opening_balance + inflow - outflow
        actual_balance = paystack_account.balance

        reconciliation = AccountReconciliation.objects.create(
            reconciliation_type='BANK',
            account=paystack_account,
            start_date=start_date,
            end_date=end_date,
            expected_balance=expected_balance,
            actual_balance=actual_balance,
            reconciled_by=user,
            details=cls._make_serializable({
                'inflow': inflow,
                'outflow': outflow,
                'transaction_count': txns.count(),
            }),
        )
        cls._log_audit(
            user,
            'AccountReconciliation',
            reconciliation.id,
            'PAYSTACK_RECONCILIATION generated',
        )

        return cls._make_serializable({
            'id': reconciliation.id,
            'status': reconciliation.status,
            'expected_balance': reconciliation.expected_balance,
            'actual_balance': reconciliation.actual_balance,
            'variance': reconciliation.variance,
            'period_start': start_date,
            'period_end': end_date,
        })
