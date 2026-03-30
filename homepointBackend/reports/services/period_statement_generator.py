# period_statement.py
from orders.models import Order
from reports.models import Report
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from payments.models import CashTransaction, MpesaTransaction




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
        # Convert to datetime for filtering if needed
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        # Ensure we have datetime objects
        if not isinstance(start_date, datetime):
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        if not isinstance(end_date, datetime):
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Overall summary
        summary = orders.aggregate(
            total_orders=Count('id'),
            completed_orders=Count('id', filter=Q(status='paid')),
            total_revenue=Sum('total_amount', filter=Q(status='paid')) or Decimal('0'),
            avg_order_value=Avg('total_amount', filter=Q(status='paid')) or Decimal('0'),
        )
        
        # Ensure total_revenue is never None
        total_revenue = summary['total_revenue'] or Decimal('0')
        total_transactions = summary['total_orders'] or 0
        
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
                status='paid'
            )
            
            day_summary = day_orders.aggregate(
                total=Sum('total_amount') or Decimal('0'),
                count=Count('id')
            )
            
            # Get daily M-Pesa and Cash breakdown
            day_mpesa_data = MpesaTransaction.objects.filter(
                timestamp__gte=day_start,
                timestamp__lte=day_end,             
                movement_type='IN',
            ).distinct().aggregate(
                mpesa_sales=Sum('amount') or Decimal('0'),
                mpesa_count=Count('id')
            )
            
            day_cash_data = CashTransaction.objects.filter(
                timestamp__gte=day_start,
                timestamp__lte=day_end,             
                movement_type='IN',
            ).distinct().aggregate(
                cash_sales=Sum('amount') or Decimal('0'),
                cash_count=Count('id')
            )
            
            daily_sales.append({
                'date': current_date.isoformat(),
                'total': str(day_summary['total']),
                'count': day_summary['count'],
                'mpesa_sales': str(day_mpesa_data['mpesa_sales']),
                'cash_sales': str(day_cash_data['cash_sales']),
                'mpesa_count': day_mpesa_data['mpesa_count'],
                'cash_count': day_cash_data['cash_count'],
            })
            
            current_date += timedelta(days=1)
        
        # Payment method breakdown
        mpesa_data = MpesaTransaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,             
            movement_type='IN',
        ).distinct().aggregate(
            mpesa_sales=Sum('amount') or Decimal('0'),
            mpesa_count=Count('id')
        )

        # Cash breakdown: Filter orders that have at least one CashTransaction
        cash_data = CashTransaction.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,             
            movement_type='IN',
        ).distinct().aggregate(
            cash_sales=Sum('amount') or Decimal('0'),
            cash_count=Count('id')
        )
        
        # Create and save report
        report = Report.objects.create(
            report_type='PERIOD_SALES',
            title=f'Sales Report: {start_date} to {end_date}',
            start_date=start_date,
            end_date=end_date,
            generated_by=user,
            status='paid',
            total_revenue=total_revenue,
            total_transactions=total_transactions,
            data={
                'summary': cls._make_serializable(summary),
                'daily_breakdown': daily_sales,
                'payment_breakdown': {
                    'mpesa': cls._make_serializable(mpesa_data),
                    'cash': cls._make_serializable(cash_data),
                },
            }
        )
        
        # Return serialized report data instead of Report object
        return cls._make_serializable({
            'id': report.id,
            'report_type': report.report_type,
            'title': report.title,
            'start_date': report.start_date.isoformat(),
            'end_date': report.end_date.isoformat(),
            'total_revenue': str(report.total_revenue),
            'total_transactions': report.total_transactions,
            'data': report.data,
        })