# period_statement.py
from orders.models import Order
from reports.models import Report
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from payments.models import CashTransaction, MpesaTransaction, PaystackTransaction




class PeriodGenerator:

    @staticmethod
    def _normalize_boundary(value, boundary):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if isinstance(value, datetime):
            return value
        return timezone.make_aware(datetime.combine(value, boundary))

    @staticmethod
    def _payment_summary(transaction_model, start_date, end_date, sales_key, count_key):
        return transaction_model.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date,
            movement_type='IN',
        ).distinct().aggregate(
            **{
                sales_key: Sum('amount') or Decimal('0'),
                count_key: Count('id'),
            }
        )

    @classmethod
    def _daily_sales(cls, orders, start_date, end_date):
        daily_sales = []
        current_date = start_date.date()
        final_date = end_date.date()

        while current_date <= final_date:
            day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
            day_end = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))
            day_summary = orders.filter(
                created_at__gte=day_start,
                created_at__lte=day_end,
                status='paid'
            ).aggregate(
                total=Sum('total_amount') or Decimal('0'),
                count=Count('id')
            )
            mpesa_data = cls._payment_summary(
                MpesaTransaction, day_start, day_end, 'mpesa_sales', 'mpesa_count'
            )
            cash_data = cls._payment_summary(
                CashTransaction, day_start, day_end, 'cash_sales', 'cash_count'
            )
            paystack_data = cls._payment_summary(
                PaystackTransaction, day_start, day_end, 'paystack_sales', 'paystack_count'
            )
            daily_sales.append({
                'date': current_date.isoformat(),
                'total': str(day_summary['total']),
                'count': day_summary['count'],
                'mpesa_sales': str(mpesa_data['mpesa_sales']),
                'cash_sales': str(cash_data['cash_sales']),
                'paystack_sales': str(paystack_data['paystack_sales']),
                'mpesa_count': mpesa_data['mpesa_count'],
                'cash_count': cash_data['cash_count'],
                'paystack_count': paystack_data['paystack_count'],
            })
            current_date += timedelta(days=1)

        return daily_sales

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
        start_date = cls._normalize_boundary(start_date, datetime.min.time())
        end_date = cls._normalize_boundary(end_date, datetime.max.time())
        
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
        
        daily_sales = cls._daily_sales(orders, start_date, end_date)
        
        # Payment method breakdown
        mpesa_data = cls._payment_summary(
            MpesaTransaction, start_date, end_date, 'mpesa_sales', 'mpesa_count'
        )

        cash_data = cls._payment_summary(
            CashTransaction, start_date, end_date, 'cash_sales', 'cash_count'
        )
        
        paystack_data = cls._payment_summary(
            PaystackTransaction, start_date, end_date, 'paystack_sales', 'paystack_count'
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
                    'paystack': cls._make_serializable(paystack_data),
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