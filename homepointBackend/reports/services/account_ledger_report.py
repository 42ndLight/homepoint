"""Account Ledger report generator."""

from payments.models import Account, Transaction
from reports.models import Report
from reports.services.base import ReportServiceMixin


class AccountLedgerReport(ReportServiceMixin):
    """Generate an ACCOUNT_LEDGER report for a single account."""

    @classmethod
    def generate_account_ledger(cls, account_id, start_date, end_date, user=None):
        start_date, end_date = cls._normalize_range(start_date, end_date)
        account = Account.objects.get(id=account_id)

        txn_list = list(
            Transaction.objects.filter(
                account=account,
                timestamp__gte=start_date,
                timestamp__lte=end_date,
                status='SUCCESS',
            ).order_by('timestamp')
        )

        # NOTE: walks backward from the CURRENT balance, so this is only
        # accurate for ranges ending now. Swap in a real opening-balance source
        # for historical ledgers.
        running_balance = account.balance
        for txn in reversed(txn_list):
            running_balance -= (
                txn.amount if txn.movement_type == 'IN' else -txn.amount
            )
        opening_balance = running_balance

        entries = []
        balance = opening_balance
        for txn in txn_list:
            balance += (
                txn.amount if txn.movement_type == 'IN' else -txn.amount
            )
            entries.append({
                'timestamp': txn.timestamp,
                'movement_type': txn.movement_type,
                'transaction_type': txn.transaction_type,
                'amount': txn.amount,
                'running_balance': balance,
                'reference_id': txn.reference_id,
                'notes': txn.notes,
            })

        report_data = {
            'account_id': account.id,
            'account_name': account.name,
            'account_type': account.account_type,
            'period_start': start_date,
            'period_end': end_date,
            'opening_balance': opening_balance,
            'closing_balance': balance,
            'entries': entries,
        }

        report = Report.objects.create(
            report_type='ACCOUNT_LEDGER',
            title=(
                f'Account Ledger ({account.account_type}): '
                f'{start_date.date()} to {end_date.date()}'
            ),
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='COMPLETED',
            data=cls._make_serializable(report_data),
        )
        cls._log_audit(user, 'Report', report.id, 'ACCOUNT_LEDGER generated')

        return cls._make_serializable({'id': report.id, **report_data})
