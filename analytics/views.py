"""
Views for the analytics app.

Provides financial summary and insight endpoints.
Analyst and Admin roles have access to these endpoints.
"""

from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAnalystOrAdmin
from services import analytics_service
from transactions.serializers import FinancialRecordSerializer


def _format_decimal(value):
    """Ensure Decimal values are JSON-serializable as strings."""
    return str(value) if isinstance(value, Decimal) else value


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAdmin])
def summary(request):
    """
    GET /api/summary/

    Returns overall financial summary:
      - total_income
      - total_expenses
      - current_balance
      - category_breakdown (grouped by category and type)

    Access: Analyst, Admin
    """
    data = analytics_service.get_full_summary(request.user)

    # Format category breakdown for response
    category_breakdown = [
        {
            'category': row['category'],
            'type': row['type'],
            'total': _format_decimal(row['total']),
            'count': row['count'],
        }
        for row in data['category_breakdown']
    ]

    return Response({
        'total_income': _format_decimal(data['total_income']),
        'total_expenses': _format_decimal(data['total_expenses']),
        'current_balance': _format_decimal(data['current_balance']),
        'category_breakdown': category_breakdown,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAdmin])
def monthly_summary(request):
    """
    GET /api/summary/monthly/

    Returns income/expense totals aggregated by calendar month.
    Most recent month is listed first.

    Access: Analyst, Admin
    """
    monthly_data = analytics_service.get_monthly_summary(request.user)

    formatted = [
        {
            'month': entry['month'],
            'income': _format_decimal(entry['income']),
            'expense': _format_decimal(entry['expense']),
            'balance': _format_decimal(entry['balance']),
            'income_count': entry['income_count'],
            'expense_count': entry['expense_count'],
        }
        for entry in monthly_data
    ]

    return Response({
        'months': len(formatted),
        'monthly_summary': formatted,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity(request):
    """
    GET /api/summary/recent/?limit=10

    Returns the most recent transactions for the current user.
    Optional query param: limit (default 10, max 50)

    Access: All authenticated users
    """
    try:
        limit = int(request.query_params.get('limit', 10))
        limit = max(1, min(limit, 50))  # clamp between 1 and 50
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid limit value. Must be an integer between 1 and 50.'},
            status=400
        )

    records = analytics_service.get_recent_activity(request.user, limit=limit)
    serializer = FinancialRecordSerializer(records, many=True)

    return Response({
        'count': len(records),
        'recent_activity': serializer.data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAdmin])
def income_total(request):
    """
    GET /api/summary/income/
    Returns total income for the current user.
    """
    total = analytics_service.get_total_income(request.user)
    return Response({'total_income': _format_decimal(total)})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAdmin])
def expense_total(request):
    """
    GET /api/summary/expenses/
    Returns total expenses for the current user.
    """
    total = analytics_service.get_total_expenses(request.user)
    return Response({'total_expenses': _format_decimal(total)})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAdmin])
def balance(request):
    """
    GET /api/summary/balance/
    Returns current balance (income - expenses).
    """
    bal = analytics_service.get_current_balance(request.user)
    return Response({'current_balance': _format_decimal(bal)})
