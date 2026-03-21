from reports.models import ReportHistory
from orders.models import Order
from payments.models import Account, CashTransaction, MpesaTransaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal

class DailySalesReport:
    
    @staticmethod
    def _make_serializable(data):
        if isinstance(data, dict):
            return {k: DailySalesReport._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DailySalesReport._make_serializable(i) for i in data]
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, (datetime, timezone.datetime)):
            return data.isoformat()
        return data


    @classmethod
    def generate_daily_sales_report(cls, report_type, date=None):
        """
        Generate comprehensive daily sales report        
        report_type: 'Z' for full day, 'X' for current status since start of day.
        date: The specific date to report on (defaults to today).
        """
        now = timezone.now()
        if report_type == 'X':
        # Find the last Z-Report generated
            last_z = ReportHistory.objects.filter(report_type='Z').latest('generated_at')
        
        # Start from last Z timestamp, or midnight if no Z exists
            if last_z:
                start_datetime = last_z.generated_at
            else:
                start_datetime = timezone.make_aware(datetime.combine(now.date(), datetime.min.time()))
            
            end_datetime = now

        else: # Z-Report Logic
            target_date = date or now.date()
            start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
            end_datetime = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
        
        # Get all orders for the day
        orders = Order.objects.filter(
            created_at__gte=start_datetime,
            created_at__lte=end_datetime
        )
                
        # Aggregate data
        summary = orders.aggregate(
            total_orders=Count('id'),
            completed_orders=Count('id', filter=Q(status='delivered')),
            pending_orders=Count('id', filter=Q(status='pending')),
            cancelled_orders=Count('id', filter=Q(status='cancelled')),
            total_revenue=Sum('total_amount', filter=Q(status='paid')) or Decimal('0'),
            
        )
        
        # Payment method breakdown
        # M-Pesa breakdown: Filter orders that have at least one MpesaTransaction
        mpesa_data = MpesaTransaction.objects.filter(
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime,             
            movement_type='IN',
        ).distinct().aggregate(
            mpesa_sales=Sum('amount') or Decimal('0'),
            mpesa_count=Count('id')
        )

        # Cash breakdown: Filter orders that have at least one CashTransaction
        cash_data = CashTransaction.objects.filter(
            timestamp__gte=start_datetime,
            timestamp__lte=end_datetime,             
            movement_type='IN',
        ).distinct().aggregate(
            cash_sales=Sum('amount') or Decimal('0'),
            cash_count=Count('id')
        )
        
        # Get account balances
        cash_account = Account.objects.filter(account_type='CASH').first()
        mpesa_account = Account.objects.filter(account_type='MPESA').first()
        
        report_data = {
            'report_type': report_type,
            'generated_at': now.isoformat(),
            'period_start': start_datetime,
            'period_end': end_datetime,
            'summary': summary,
            'payment_breakdown': {
                'mpesa': mpesa_data,
                'cash': cash_data,
            },  
            'account_balances': {
                'cash': cash_account.balance if cash_account else '0.00',
                'mpesa': mpesa_account.balance if mpesa_account else '0.00',
            },
            'orders': list(orders.values(
                'id', 'total_amount', 'status', 
                'created_at', 'phone_number'
            ))
        }
        
        return cls._make_serializable(report_data)