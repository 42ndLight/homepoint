"""User Performance report generator."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum, Avg
from decimal import Decimal

from payments.models import Transaction
from reports.models import Report
from reports.services.base import ReportServiceMixin


User = get_user_model()


class UserPerformanceReport(ReportServiceMixin):
    """Generate a USER_PERFORMANCE report from successful sales transactions."""

    @classmethod
    def generate_user_performance_report(cls, start_date, end_date, user=None):
        start_date, end_date = cls._normalize_range(start_date, end_date)

        txns = Transaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            movement_type='IN',
            status='SUCCESS',
            transaction_type='SALES',
        )

        performance = (
            txns.values('user')
            .annotate(
                total_transactions=Count('id'),
                total_revenue=Sum('amount'),
                avg_transaction_value=Avg('amount'),
            )
            .order_by('-total_revenue')
        )

        user_ids = [p['user'] for p in performance if p['user']]
        user_lookup = {
            u.id: (u.get_full_name() or u.username)
            for u in User.objects.filter(id__in=user_ids)
        }

        results = [
            {
                'user_id': row['user'],
                'user_name': user_lookup.get(row['user'], 'Unknown'),
                'total_transactions': row['total_transactions'],
                'total_revenue': row['total_revenue'] or Decimal('0'),
                'avg_transaction_value': row['avg_transaction_value'] or Decimal('0'),
            }
            for row in performance
        ]

        report_data = {
            'period_start': start_date,
            'period_end': end_date,
            'staff_performance': results,
        }

        report = Report.objects.create(
            report_type='USER_PERFORMANCE',
            title=f'User Performance Report: {start_date.date()} to {end_date.date()}',
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='COMPLETED',
            data=cls._make_serializable(report_data),
        )
        cls._log_audit(user, 'Report', report.id, 'USER_PERFORMANCE generated')

        return cls._make_serializable({'id': report.id, **report_data})
