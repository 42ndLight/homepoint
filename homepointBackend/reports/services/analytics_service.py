from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Cast
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from orders.models import Order, OrderItem
from products.models import Variant


class AnalyticsService:
    """Service for calculating analytics data from orders and inventory"""

    @staticmethod
    def get_top_products(start_date, end_date, limit=10):
        # 1. Build the filter once to keep it DRY
        filters = {
            'order__created_at__gte': start_date,
            'order__created_at__lte': end_date,
            'order__status__in': ['paid', 'delivered']
        }

        # 2. Use F expression to calculate row-level revenue, then Sum it
        top_products = (
            OrderItem.objects.filter(**filters)
            .values(
                'variant__sku',
                'variant__product__name',
            )
            .annotate(
                total_quantity=Sum('quantity'),
                # Multiply price * qty for each row, then sum them up
                total_revenue=Sum(
                    F('price_at_purchase') * F('quantity'), 
                    output_field=DecimalField()
                )
            )
            .order_by('-total_quantity')[:limit]
        )

        # 3. Format the results (No extra queries needed!)
        return [
            {
                'product_name': item['variant__product__name'],
                'sku': item['variant__sku'],
                'quantity': item['total_quantity'],
                'revenue': str(item['total_revenue'])
            } 
            for item in top_products
        ]

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

