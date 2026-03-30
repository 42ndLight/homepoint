from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.utils import timezone
from datetime import datetime, timedelta, date
from reports.models import DailySalesSnapshot
from reports.services.analytics_service import AnalyticsService
from reports.services.period_statement_generator import PeriodGenerator


class AnalyticsView(APIView):
    """
    GET /api/reports/analytics/?start_date=2024-03-20&end_date=2024-03-27
    
    Returns aggregated sales analytics data including:
    - Daily revenue breakdown (from PeriodGenerator)
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

            # Use PeriodGenerator to get comprehensive report data
            period_report = PeriodGenerator.generate_period_sales_report(start_date, end_date)

            # Extract data from nested structure
            data_container = period_report.get('data', {})
            
            # Transform daily breakdown to match dashboard format
            period_daily = data_container.get('daily_breakdown', [])
            daily_revenue = []
            
            for day in period_daily:
                daily_revenue.append({
                    'date': day.get('date'),
                    'total_sales': day.get('total', '0'),
                    'total_orders': day.get('count', 0),
                    'mpesa_sales': day.get('mpesa_sales', '0'),
                    'cash_sales': day.get('cash_sales', '0'),
                    'mpesa_count': day.get('mpesa_count', 0),
                    'cash_count': day.get('cash_count', 0),
                })
            
            # Extract payment breakdown
            payment_breakdown = data_container.get('payment_breakdown', {})

            # Extract and format summary for dashboard
            period_summary = data_container.get('summary', {})
            summary = {
                'total_revenue': str(period_summary.get('total_revenue', '0')),
                'total_orders': period_summary.get('total_orders', 0),
                'average_order_value': str(period_summary.get('avg_order_value', '0')),
                'total_mpesa': str(payment_breakdown.get('mpesa', {}).get('mpesa_sales', '0')),
                'total_cash': str(payment_breakdown.get('cash', {}).get('cash_sales', '0')),
            }

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

