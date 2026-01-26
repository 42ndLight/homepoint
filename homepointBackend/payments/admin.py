from django.contrib import admin
from .models import Transaction, MpesaTransaction, CashTransaction

# Register your models here.

admin.site.register(Transaction)
admin.site.register(MpesaTransaction)
admin.site.register(CashTransaction)    

