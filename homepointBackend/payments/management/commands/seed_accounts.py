#seed_accounts.py

from django.core.management.base import BaseCommand
from payments.models import Account

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        accounts = [
            ('Cash Office', 'CASH'),
            ('M-Pesa Paybill', 'MPESA'),
            ('Bank Account', 'BANK'),
            ('Sales Revenue', 'REVENUE'),
            ('Expenses', 'EXPENSE'),
        ]
        for name, atype in accounts:
            Account.objects.get_or_create(account_type=atype, defaults={'name': name})
        self.stdout.write("Accounts seeded.")