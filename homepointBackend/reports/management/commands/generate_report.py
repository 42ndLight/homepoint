"""Management command to generate reports and emit JSON."""

import json
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from reports.services import (
    AccountLedgerReport,
    CashFlowReport,
    DailySalesReport,
    PaystackReconciliationReport,
    PeriodGenerator,
    ProductSalesReport,
    TaxReport,
    UserPerformanceReport,
)

User = get_user_model()


REPORT_CHOICES = [
    'DAILY_SALES',
    'PERIOD_SALES',
    'CASH_FLOW',
    'PAYSTACK_RECONCILIATION',
    'ACCOUNT_LEDGER',
    'USER_PERFORMANCE',
    'PRODUCT_SALES',
    'TAX_REPORT',
]


class Command(BaseCommand):
    help = 'Generate a report and output it as JSON.'

    def add_arguments(self, parser):
        parser.add_argument(
            'report_type',
            choices=REPORT_CHOICES,
            help='Type of report to generate.',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (ISO format, e.g. 2026-01-01). Defaults to today.',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (ISO format, e.g. 2026-01-31). Defaults to today.',
        )
        parser.add_argument(
            '--account-id',
            type=int,
            help='Account ID (required for ACCOUNT_LEDGER).',
        )
        parser.add_argument(
            '--daily-report-type',
            type=str,
            choices=['X', 'Z'],
            default='Z',
            help="Daily report variant: 'X' since last Z, 'Z' full day. Only used for DAILY_SALES.",
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user generating the report.',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Path to write JSON output. If omitted, prints to stdout.',
        )
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='JSON indentation level.',
        )

    def handle(self, *args, **options):
        report_type = options['report_type']
        user = self._get_user(options.get('user_id'))

        if report_type == 'DAILY_SALES':
            target_date = self._parse_date_option(options.get('start_date')) or timezone.now().date()
            data = DailySalesReport.generate_daily_sales_report(
                report_type=options['daily_report_type'],
                date=target_date,
            )
        else:
            start_date, end_date = self._get_date_range(options)

            if report_type == 'PERIOD_SALES':
                data = PeriodGenerator.generate_period_sales_report(
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            elif report_type == 'CASH_FLOW':
                data = CashFlowReport.generate_cash_flow_statement(
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            elif report_type == 'PAYSTACK_RECONCILIATION':
                data = PaystackReconciliationReport.generate_paystack_reconciliation(
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            elif report_type == 'ACCOUNT_LEDGER':
                account_id = options.get('account_id')
                if account_id is None:
                    raise CommandError('--account-id is required for ACCOUNT_LEDGER')
                data = AccountLedgerReport.generate_account_ledger(
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            elif report_type == 'USER_PERFORMANCE':
                data = UserPerformanceReport.generate_user_performance_report(
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            elif report_type == 'PRODUCT_SALES':
                data = ProductSalesReport.generate_product_sales_analysis(
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            elif report_type == 'TAX_REPORT':
                data = TaxReport.generate_tax_report(
                    start_date=start_date,
                    end_date=end_date,
                    user=user,
                )
            else:
                raise CommandError(f'Unsupported report type: {report_type}')

        json_output = json.dumps(data, indent=options['indent'])

        if options.get('output'):
            with open(options['output'], 'w') as f:
                f.write(json_output)
            self.stdout.write(self.style.SUCCESS(f'Report written to {options["output"]}'))
        else:
            self.stdout.write(json_output)

    def _get_user(self, user_id):
        if user_id is None:
            return None
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f'User with id {user_id} does not exist')

    def _parse_date_option(self, value):
        if not value:
            return None
        return date.fromisoformat(value)

    def _get_date_range(self, options):
        today = timezone.now().date()
        start = self._parse_date_option(options.get('start_date')) or today
        end = self._parse_date_option(options.get('end_date')) or today

        if end < start:
            raise CommandError('end-date must be on or after start-date')

        return start, end
