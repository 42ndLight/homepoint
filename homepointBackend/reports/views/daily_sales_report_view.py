
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime
from reports.models import ReportHistory
from reports.services.daily_report_generator import DailySalesReport


# Create your views here.
class DailySalesReportView(APIView):
    """
    GET /api/reports/daily-sales/?date=2024-01-15
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        date_str = request.query_params.get('date')
        report_type = request.query_params.get('report_type').upper()

        if report_type not in ['X', 'Z']:
            return Response(
                {'error': 'Invalid report type. Use "X" for current snapshot or "Z" for full day.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            report_date = timezone.now().date()
        
        
        report_data = DailySalesReport.generate_daily_sales_report(report_type, report_date)

        if report_type == 'Z':
            ReportHistory.objects.create(
                report_type='Z',
                data=report_data
            )
        
        return Response({
            'success': True,
            'report': report_data

        })