#transactions_views.py
from payments.serializers import TransactionHistorySerializer
from rest_framework.permissions import IsAuthenticated
from payments.models import Transaction
from rest_framework import generics


class TransactionHistoryListView(generics.ListAPIView):
    serializer_class = TransactionHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Transaction.objects.select_subclasses().all()
        return Transaction.objects.filter(user=self.request.user)
