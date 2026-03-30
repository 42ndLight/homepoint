from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.utils import timezone
from datetime import datetime, timedelta
from reports.models import DailySalesSnapshot
from reports.services.analytics_service import AnalyticsService


class AnalyticsView(APIView):
    """
    GET /api/reports/analytics/?start_date=2024-03-20&end_date=2024-03-27
    
    Returns aggregated sales analytics data including:
    - Daily revenue breakdown
    - Top selling products
    - Summary metrics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Parse query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            limit = int(request.query_params.get('limit', 10))

            # Default date range: last 7 days
            today = timezone.now().date()
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                end_date = today

            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                start_date = end_date - timedelta(days=7)

            # Validate date range
            if start_date > end_date:
                return Response(
                    {'error': 'start_date must be before or equal to end_date'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Fetch daily sales snapshots
            daily_snapshots = DailySalesSnapshot.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')

            # Convert to serializable format
            daily_revenue = []
            for snapshot in daily_snapshots:
                daily_revenue.append({
                    'date': snapshot.date.isoformat(),
                    'total_sales': str(snapshot.total_sales),
                    'total_orders': snapshot.total_orders,
                    'completed_orders': snapshot.completed_orders,
                    'cancelled_orders': snapshot.cancelled_orders,
                    'mpesa_sales': str(snapshot.mpesa_sales),
                    'cash_sales': str(snapshot.cash_sales),
                    'mpesa_count': snapshot.mpesa_count,
                    'cash_count': snapshot.cash_count,
                    'total_vat': str(snapshot.total_vat),
                    'cash_balance': str(snapshot.cash_balance),
                    'mpesa_balance': str(snapshot.mpesa_balance),
                })

            # Get top products
            start_datetime = timezone.make_aware(
                datetime.combine(start_date, datetime.min.time())
            )
            end_datetime = timezone.make_aware(
                datetime.combine(end_date, datetime.max.time())
            )
            top_products = AnalyticsService.get_top_products(
                start_datetime, 
                end_datetime, 
                limit
            )

            # Calculate summary metrics
            summary = AnalyticsService.calculate_summary_metrics(daily_revenue)

            return Response({
                'success': True,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                },
                'daily_revenue': daily_revenue,
                'top_products': top_products,
                'summary': summary,
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
