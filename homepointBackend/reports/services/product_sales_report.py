"""Product Sales Analysis report generator."""

from django.db.models import DecimalField, F, Sum
from decimal import Decimal

from orders.models import OrderItem
from reports.models import Report
from reports.services.base import ReportServiceMixin


class ProductSalesReport(ReportServiceMixin):
    """Generate a PRODUCT_SALES report for a date range."""

    @classmethod
    def generate_product_sales_analysis(cls, start_date, end_date, user=None):
        start_date, end_date = cls._normalize_range(start_date, end_date)

        line_items = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__status__in=['paid', 'delivered'],
        )

        product_breakdown = (
            line_items.values('variant__sku', 'variant__product__name')
            .annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(
                    F('price_at_purchase') * F('quantity'),
                    output_field=DecimalField(),
                ),
            )
            .order_by('-total_revenue')
        )

        results = [
            {
                'product_name': item['variant__product__name'],
                'sku': item['variant__sku'],
                'quantity': item['total_quantity'],
                'revenue': item['total_revenue'] or Decimal('0'),
            }
            for item in product_breakdown
        ]

        total_revenue = sum(
            (item['revenue'] for item in results), Decimal('0')
        )
        total_units = sum((item['quantity'] or 0) for item in results)

        report_data = {
            'period_start': start_date,
            'period_end': end_date,
            'products': results,
            'total_revenue': total_revenue,
            'total_units_sold': total_units,
        }

        report = Report.objects.create(
            report_type='PRODUCT_SALES',
            title=f'Product Sales Analysis: {start_date.date()} to {end_date.date()}',
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='COMPLETED',
            total_revenue=total_revenue,
            data=cls._make_serializable(report_data),
        )
        cls._log_audit(user, 'Report', report.id, 'PRODUCT_SALES generated')

        return cls._make_serializable({'id': report.id, **report_data})
