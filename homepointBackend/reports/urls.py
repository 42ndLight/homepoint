from django.urls import path
from .views.daily_sales_report_view import DailySalesReportView
from .views.analytics_view import AnalyticsView


urlpatterns = [
    path('daily-sales/', DailySalesReportView.as_view(), name='daily-sales-report'),
    path('period_statement/', DailySalesReportView.as_view(), name='daily-sales-report'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]