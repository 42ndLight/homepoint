from orders.models import Order
from payments.models import Account
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

class DailySalesReport:

    @staticmethod
    def generate_daily_sales_report(date=None):
        """
        Generate comprehensive daily sales report
        """
        if date is None:
            date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        # Get all orders for the day
        orders = Order.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
        
        # Aggregate data
        summary = orders.aggregate(
            total_orders=Count('id'),
            completed_orders=Count('id', filter=Q(status='COMPLETED')),
            pending_orders=Count('id', filter=Q(status='PENDING')),
            cancelled_orders=Count('id', filter=Q(status='CANCELLED')),
            total_revenue=Sum('total_amount', filter=Q(status='COMPLETED')) or Decimal('0'),
            total_vat=Sum('vat', filter=Q(status='COMPLETED')) or Decimal('0'),
        )
        
        # Payment method breakdown
        mpesa_data = orders.filter(payment_method='mpesa', status='COMPLETED').aggregate(
            mpesa_sales=Sum('total_amount') or Decimal('0'),
            mpesa_count=Count('id')
        )
        
        cash_data = orders.filter(payment_method='cash', status='COMPLETED').aggregate(
            cash_sales=Sum('total_amount') or Decimal('0'),
            cash_count=Count('id')
        )
        
        # Get account balances
        cash_account = Account.objects.filter(account_type='CASH').first()
        mpesa_account = Account.objects.filter(account_type='MPESA').first()
        
        report_data = {
            'date': date.isoformat(),
            'summary': summary,
            'payment_methods': {
                'mpesa': mpesa_data,
                'cash': cash_data,
            },
            'account_balances': {
                'cash': str(cash_account.balance) if cash_account else '0.00',
                'mpesa': str(mpesa_account.balance) if mpesa_account else '0.00',
            },
            'orders': list(orders.values(
                'id', 'total_amount', 'payment_method', 'status', 
                'created_at', 'phone_number'
            ))
        }
        
        return report_data