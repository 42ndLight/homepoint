"""Cash Flow Statement report generator."""

from django.db.models import Sum
from decimal import Decimal

from payments.models import Account, Transaction
from reports.models import Report
from reports.services.base import ReportServiceMixin


class CashFlowReport(ReportServiceMixin):
    """Generate a CASH_FLOW report per account over a date range."""

    @classmethod
    def generate_cash_flow_statement(cls, start_date, end_date, user=None):
        start_date, end_date = cls._normalize_range(start_date, end_date)

        accounts = Account.objects.all()
        account_flows = []
        total_inflow = Decimal('0')
        total_outflow = Decimal('0')

        for account in accounts:
            txns = Transaction.objects.filter(
                account=account,
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
            net_change = inflow - outflow

            # NOTE: account.balance is the CURRENT balance. For historical
            # accuracy, seed opening_balance from a DailySalesSnapshot or
            # stored opening balance instead.
            opening_balance = account.balance - net_change
            closing_balance = account.balance

            account_flows.append({
                'account_id': account.id,
                'account_name': account.name,
                'account_type': account.account_type,
                'opening_balance': opening_balance,
                'inflow': inflow,
                'outflow': outflow,
                'net_change': net_change,
                'closing_balance': closing_balance,
            })
            total_inflow += inflow
            total_outflow += outflow

        report_data = {
            'period_start': start_date,
            'period_end': end_date,
            'accounts': account_flows,
            'total_inflow': total_inflow,
            'total_outflow': total_outflow,
            'net_cash_flow': total_inflow - total_outflow,
        }

        report = Report.objects.create(
            report_type='CASH_FLOW',
            title=f'Cash Flow Statement: {start_date.date()} to {end_date.date()}',
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='COMPLETED',
            total_revenue=total_inflow,
            data=cls._make_serializable(report_data),
        )
        cls._log_audit(user, 'Report', report.id, 'CASH_FLOW generated')

        return cls._make_serializable({'id': report.id, **report_data})
