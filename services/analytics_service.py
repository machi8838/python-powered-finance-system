"""
services/analytics_service.py

Business logic for financial summaries and analytics.
All calculations are performed at the database query level for efficiency.
"""

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from decimal import Decimal
from transactions.models import FinancialRecord


def _zero():
    return Decimal('0.00')


def get_total_income(user) -> Decimal:
    """Sum of all income records for a user."""
    result = FinancialRecord.objects.filter(
        user=user, type=FinancialRecord.TransactionType.INCOME
    ).aggregate(total=Sum('amount'))
    return result['total'] or _zero()


def get_total_expenses(user) -> Decimal:
    """Sum of all expense records for a user."""
    result = FinancialRecord.objects.filter(
        user=user, type=FinancialRecord.TransactionType.EXPENSE
    ).aggregate(total=Sum('amount'))
    return result['total'] or _zero()


def get_current_balance(user) -> Decimal:
    """Current balance = total income minus total expenses."""
    return get_total_income(user) - get_total_expenses(user)


def get_category_breakdown(user) -> list:
    """
    Returns totals grouped by category across all transaction types.
    Each entry has category, type, and total amount.
    """
    breakdown = (
        FinancialRecord.objects
        .filter(user=user)
        .values('category', 'type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('category', 'type')
    )
    return list(breakdown)


def get_monthly_summary(user) -> list:
    """
    Aggregates income and expense totals per calendar month.
    Returns a list sorted by month descending (most recent first).
    """
    monthly = (
        FinancialRecord.objects
        .filter(user=user)
        .annotate(month=TruncMonth('date'))
        .values('month', 'type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-month', 'type')
    )

    # Pivot into month → {income, expense} structure
    pivot = {}
    for row in monthly:
        month_key = row['month'].strftime('%Y-%m') if row['month'] else 'unknown'
        if month_key not in pivot:
            pivot[month_key] = {
                'month': month_key,
                'income': _zero(),
                'expense': _zero(),
                'income_count': 0,
                'expense_count': 0,
            }
        if row['type'] == 'income':
            pivot[month_key]['income'] = row['total']
            pivot[month_key]['income_count'] = row['count']
        else:
            pivot[month_key]['expense'] = row['total']
            pivot[month_key]['expense_count'] = row['count']

    result = list(pivot.values())
    for entry in result:
        entry['balance'] = entry['income'] - entry['expense']

    return sorted(result, key=lambda x: x['month'], reverse=True)


def get_recent_activity(user, limit: int = 10) -> list:
    """
    Returns the most recent transactions for a user, ordered by date descending.
    """
    records = (
        FinancialRecord.objects
        .filter(user=user)
        .order_by('-date', '-created_at')
        [:limit]
    )
    return list(records)


def get_full_summary(user) -> dict:
    """
    Aggregates all summary data in one call.
    Used by the /api/summary/ endpoint.
    """
    total_income = get_total_income(user)
    total_expenses = get_total_expenses(user)

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'current_balance': total_income - total_expenses,
        'category_breakdown': get_category_breakdown(user),
    }
