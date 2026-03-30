# period_generator.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime
from reports.services.period_statement_generator import PeriodGenerator



class PeriodSalesStatementView(APIView):

	def get(self, request):
		start_date_str = request.query_params.get('start_date')
		end_date_str = request.query_params.get('end_date')

		# Default to today if not provided
		if not start_date_str or not end_date_str:
			start_date = timezone.now().date()
			end_date = timezone.now().date()
		else:
			try:
				start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
				end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
			except ValueError:
				return Response(
					{'error' : 'Invalid date Format. Use YYYY-MM-DD'},
					status=status.HTTP_400_BAD_REQUEST
				)

		report_data = PeriodGenerator.generate_period_sales_report(start_date, end_date)

		return Response({
            	'success': True,
            	'report': report_data	
        	})




