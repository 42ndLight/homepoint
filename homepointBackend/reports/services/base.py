"""Shared helpers for report generators."""

from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from reports.models import AuditLog


class ReportServiceMixin:
    """Shared serialization, date coercion, and audit helpers."""

    @staticmethod
    def _make_serializable(data):
        if isinstance(data, dict):
            return {k: ReportServiceMixin._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [ReportServiceMixin._make_serializable(i) for i in data]
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, (datetime, timezone.datetime)):
            return data.isoformat()
        return data

    @staticmethod
    def _normalize_range(start_date, end_date):
        """Coerce str/date -> aware full-day datetimes."""
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        if not isinstance(start_date, datetime):
            start_date = timezone.make_aware(
                datetime.combine(start_date, datetime.min.time())
            )
        if not isinstance(end_date, datetime):
            end_date = timezone.make_aware(
                datetime.combine(end_date, datetime.max.time())
            )
        return start_date, end_date

    @staticmethod
    def _log_audit(user, model_name, object_id, notes):
        """Record report generation in the audit trail."""
        AuditLog.objects.create(
            action_type='REPORT_GENERATED',
            model_name=model_name,
            object_id=object_id,
            user=user,
            notes=notes,
        )
