from django.contrib import admin

from .models import Report, DailySalesSnapshot, ReportSchedule, AccountReconciliation, AuditLog


# Register your models here
admin.site.register(Report)
admin.site.register(DailySalesSnapshot)
admin.site.register(ReportSchedule)
admin.site.register(AccountReconciliation)
admin.site.register(AuditLog)
