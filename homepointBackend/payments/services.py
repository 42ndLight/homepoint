#services.py

from django.db import transaction as db_transaction
from django.db.models import F
from .models import (
    Account, Transaction,
    SaleTransaction, MpesaTransaction,
    CashTransaction, ExpenseTransaction,
    DepositWithdrawal,
)

def _debit_account(account, amount):
    """Take money OUT of an account. Raises if insufficient funds."""
    if account.balance < amount:
        raise ValueError(f"Insufficient balance in '{account.name}': "
                         f"{account.balance} < {amount}")
    account.balance = F('balance') - amount
    account.save(update_fields=['balance'])
    account.refresh_from_db()


def _credit_account(account, amount):
    """Put money INTO an account."""
    account.balance = F('balance') + amount
    account.save(update_fields=['balance'])
    account.refresh_from_db()


def _get_account(account_type):
    """Fetch and lock account row for the duration of the transaction."""
    return Account.objects.select_for_update().get(account_type=account_type)


def _build_transaction(model_class, account, user, movement, tx_type, amount, extra_fields):
    """
    Core ledger writer. Creates any Transaction subtype.
    All services funnel through here — one place to change auditing logic.
    """
    return model_class.objects.create(
        account=account,
        user=user,
        movement_type=movement,
        transaction_type=tx_type,
        amount=amount,
        balance_after=account.balance,  # account already refreshed before this call
        **extra_fields,
    )


@db_transaction.atomic
def record_cash_sale(user, order, amount, receipt_number='', notes=''):
    cash    = _get_account('CASH')
    revenue = _get_account('REVENUE')

    _credit_account(cash, amount)
    _credit_account(revenue, amount)

    tx = _build_transaction(
        model_class=CashTransaction,
        account=cash,
        user=user,
        movement='IN',
        tx_type='SALE',
        amount=amount,
        extra_fields={
            'order': order,
            'receipt_number': receipt_number,
            'recorded_by': user,
            'notes': notes,
        }
    )

    order.status = 'paid'
    order.save(update_fields=['status'])
    return tx


@db_transaction.atomic
def record_mpesa_sale(user, order, amount, phone_number,
                      checkout_request_id, mpesa_receipt='', callback_data=None):
    mpesa   = _get_account('MPESA')
    revenue = _get_account('REVENUE')

    _credit_account(mpesa, amount)
    _credit_account(revenue, amount)

    tx = _build_transaction(
        model_class=MpesaTransaction,
        account=mpesa,
        user=user,
        movement='IN',
        tx_type='SALE',
        amount=amount,
        extra_fields={
            'order': order,
            'checkout_request_id': checkout_request_id,
            'mpesa_receipt_number': mpesa_receipt,
            'phone_number': phone_number,
            'status': 'SUCCESS',
            'callback_data': callback_data,
        }
    )

    order.status = 'paid'
    order.save(update_fields=['status'])
    return tx


@db_transaction.atomic
def record_mpesa_initiated(order, amount, phone_number, checkout_request_id, user):
    """Call this when STK push is sent — before callback arrives."""
    mpesa = _get_account('MPESA')

    # Don't touch balance yet — payment not confirmed
    return MpesaTransaction.objects.create(
        account=mpesa,
        user=user,
        movement_type='IN',
        transaction_type='SALE',
        amount=amount,
        balance_after=mpesa.balance,  # snapshot, will be wrong until confirmed — acceptable
        order=order,
        checkout_request_id=checkout_request_id,
        phone_number=phone_number,
        status='PENDING',
    )


@db_transaction.atomic
def confirm_mpesa_payment(checkout_request_id, mpesa_receipt, callback_data):
    """Call this from the M-Pesa callback view."""
    mpesa_tx = MpesaTransaction.objects.select_for_update().get(
        checkout_request_id=checkout_request_id
    )

    if mpesa_tx.status != 'PENDING':
        raise ValueError(f"Transaction {checkout_request_id} already processed.")

    mpesa   = _get_account('MPESA')
    revenue = _get_account('REVENUE')

    _credit_account(mpesa, mpesa_tx.amount)
    _credit_account(revenue, mpesa_tx.amount)

    mpesa_tx.status = 'SUCCESS'
    mpesa_tx.mpesa_receipt_number = mpesa_receipt
    mpesa_tx.balance_after = mpesa.balance
    mpesa_tx.callback_data = callback_data
    mpesa_tx.save(update_fields=['status', 'mpesa_receipt_number', 'balance_after', 'callback_data'])

    mpesa_tx.order.status = 'paid'
    mpesa_tx.order.save(update_fields=['status'])

    return mpesa_tx


@db_transaction.atomic
def record_expense(user, amount, category, source_account_type='CASH',
                   supplier='', notes='', approved_by=None):
    source  = _get_account(source_account_type)
    expense = _get_account('EXPENSE')

    _debit_account(source, amount)
    _credit_account(expense, amount)

    return _build_transaction(
        model_class=ExpenseTransaction,
        account=source,
        user=user,
        movement='OUT',
        tx_type='EXPENSE',
        amount=amount,
        extra_fields={
            'category': category,
            'supplier': supplier,
            'notes': notes,
            'approved_by': approved_by,
        }
    )


@db_transaction.atomic
def record_deposit(user, amount, authorized_by,
                   source_account_type='CASH', dest_account_type='BANK', notes=''):
    source = _get_account(source_account_type)
    dest   = _get_account(dest_account_type)

    _debit_account(source, amount)
    _credit_account(dest, amount)

    return _build_transaction(
        model_class=DepositWithdrawal,
        account=source,
        user=user,
        movement='OUT',
        tx_type='DEPOSIT',
        amount=amount,
        extra_fields={
            'destination_account': dest,
            'authorized_by': authorized_by,
            'notes': notes,
        }
    )


@db_transaction.atomic
def record_withdrawal(user, amount, authorized_by,
                      source_account_type='BANK', notes=''):
    source = _get_account(source_account_type)
    cash   = _get_account('CASH')

    _debit_account(source, amount)
    _credit_account(cash, amount)

    return _build_transaction(
        model_class=DepositWithdrawal,
        account=source,
        user=user,
        movement='OUT',
        tx_type='WITHDRAWAL',
        amount=amount,
        extra_fields={
            'destination_account': cash,
            'authorized_by': authorized_by,
            'notes': notes,
        }
    )
    