from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import SmsNotification


class Command(BaseCommand):
    help = 'Delete SMS notification records older than the retention period (90 days by default).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Retention period in days (default: 90).',
        )

    def handle(self, *args, **options):
        days = options['days']
        if days < 0:
            raise ValueError('--days must not be negative')

        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = SmsNotification.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} SMS notification(s).'))
