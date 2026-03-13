from django.contrib import admin
from .models import Transaction, MpesaTransaction, CashTransaction, Account

# Register your models here.

admin.site.register(Transaction)
admin.site.register(MpesaTransaction)
admin.site.register(CashTransaction)
admin.site.register(Account)    

