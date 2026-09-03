"""Tax (VAT) report generator."""

from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP

from orders.models import Order
from reports.models import Report
from reports.services.base import ReportServiceMixin


# Standard KRA VAT rate, confirmed current for 2026.
VAT_RATE = Decimal('0.16')


class TaxReport(ReportServiceMixin):
    """Generate a TAX_REPORT (VAT summary) for a date range."""

    @classmethod
    def generate_tax_report(cls, start_date, end_date, user=None, vat_rate=VAT_RATE):
        start_date, end_date = cls._normalize_range(start_date, end_date)

        paid_orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status='paid',
        )
        gross_sales = (
            paid_orders.aggregate(total=Sum('total_amount'))['total']
            or Decimal('0')
        )

        # VAT-inclusive gross -> net = gross / (1 + rate); vat = gross - net
        net_sales = (gross_sales / (Decimal('1') + vat_rate)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        vat_payable = (gross_sales - net_sales).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        report_data = {
            'period_start': start_date,
            'period_end': end_date,
            'vat_rate': str(vat_rate),
            'gross_sales': gross_sales,
            'net_sales': net_sales,
            'vat_payable': vat_payable,
            'order_count': paid_orders.count(),
        }

        report = Report.objects.create(
            report_type='TAX_REPORT',
            title=f'VAT Report: {start_date.date()} to {end_date.date()}',
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='COMPLETED',
            total_revenue=gross_sales,
            data=cls._make_serializable(report_data),
        )
        cls._log_audit(user, 'Report', report.id, 'TAX_REPORT generated')

        return cls._make_serializable({'id': report.id, **report_data})
