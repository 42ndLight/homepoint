# period_statement.py
from orders.models import Order
from reports.models import Report
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal



class PeriodGenerator:

    @staticmethod
    def _make_serializable(data):
        if isinstance(data, dict):
            return {k: PeriodGenerator._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [PeriodGenerator._make_serializable(i) for i in data]
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, (datetime, timezone.datetime)):
            return data.isoformat()
        return data
    
    @classmethod
    def generate_period_sales_report(cls, start_date, end_date, user=None):
        """
        Generate sales report for a date range
        """
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Overall summary
        summary = orders.aggregate(
            total_orders=Count('id'),
            completed_orders=Count('id', filter=Q(status='COMPLETED')),
            total_revenue=Sum('total_amount', filter=Q(status='COMPLETED')) or Decimal('0'),
            total_vat=Sum('vat', filter=Q(status='COMPLETED')) or Decimal('0'),
            avg_order_value=Avg('total_amount', filter=Q(status='COMPLETED')) or Decimal('0'),
        )
        
        # Daily breakdown
        daily_sales = []
        current_date = start_date.date()
        end = end_date.date()
        
        while current_date <= end:
            day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
            day_end = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))
            
            day_orders = orders.filter(
                created_at__gte=day_start,
                created_at__lte=day_end,
                status='COMPLETED'
            )
            
            day_summary = day_orders.aggregate(
                total=Sum('total_amount') or Decimal('0'),
                count=Count('id')
            )
            
            daily_sales.append({
                'date': current_date.isoformat(),
                'total': str(day_summary['total']),
                'count': day_summary['count'],
            })
            
            current_date += timedelta(days=1)
        
        # Payment method breakdown
        '''payment_breakdown = orders.filter(status='COMPLETED').values('payment_method').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        )'''
        
        # Create and save report
        report = Report.objects.create(
            report_type='PERIOD_SALES',
            title=f'Sales Report: {start_date.date()} to {end_date.date()}',
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='COMPLETED',
            total_revenue=summary['total_revenue'],
            total_transactions=summary['total_orders'],
            data={
                'summary': summary,
                'daily_breakdown': daily_sales,
                'payment_breakdown': list(payment_breakdown),
            }
        )
        
        return cls._make_serializable(report)