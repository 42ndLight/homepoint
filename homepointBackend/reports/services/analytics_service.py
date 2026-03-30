from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from orders.models import Order, OrderItem
from products.models import Variant


class AnalyticsService:
    """Service for calculating analytics data from orders and inventory"""

    @staticmethod
    def get_top_products(start_date, end_date, limit=10):
        """
        Get top N products by quantity sold within date range
        
        Args:
            start_date: datetime object for start of range
            end_date: datetime object for end of range
            limit: number of top products to return (default 10)
        
        Returns:
            List of dicts with product info and sales metrics
        """
        top_products = OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__status__in=['paid', 'delivered']  # Only completed/paid orders
        ).values(
            'variant__sku',
            'variant__product__name',
        ).annotate(
            quantity=Sum('quantity'),
            revenue=Sum(F('price_at_purchase') * F('quantity'))
        ).order_by('-quantity')[:limit]

        result = []
        for item in top_products:
            result.append({
                'product_name': item['variant__product__name'],
                'sku': item['variant__sku'],
                'quantity': item['quantity'],
                'revenue': str(item['revenue'] or 0)
            })

        return result

    @staticmethod
    def calculate_summary_metrics(daily_data):
        """
        Calculate summary metrics from daily sales snapshots
        
        Args:
            daily_data: list of dicts with daily sales info
        
        Returns:
            Dict with aggregated metrics
        """
        total_revenue = sum(
            Decimal(item.get('total_sales', 0)) 
            for item in daily_data
        )
        total_orders = sum(
            item.get('total_orders', 0) 
            for item in daily_data
        )
        total_mpesa = sum(
            Decimal(item.get('mpesa_sales', 0)) 
            for item in daily_data
        )
        total_cash = sum(
            Decimal(item.get('cash_sales', 0)) 
            for item in daily_data
        )

        avg_order_value = (
            total_revenue / total_orders 
            if total_orders > 0 
            else Decimal('0')
        )

        return {
            'total_revenue': str(total_revenue),
            'total_orders': total_orders,
            'average_order_value': str(avg_order_value.quantize(Decimal('0.01'))),
            'total_mpesa': str(total_mpesa),
            'total_cash': str(total_cash),
        }

    @staticmethod
    def _make_serializable(data):
        """Convert Decimal and datetime objects to JSON-serializable types"""
        if isinstance(data, dict):
            return {k: AnalyticsService._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [AnalyticsService._make_serializable(i) for i in data]
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, (datetime, timezone.datetime)):
            return data.isoformat()
        return data
