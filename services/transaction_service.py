"""
services/transaction_service.py

Business logic layer for financial record operations.
Keeps views thin and logic reusable/testable.
"""

from django.db.models import Q
from transactions.models import FinancialRecord


def get_user_records(user):
    """Return all financial records owned by a given user."""
    return FinancialRecord.objects.filter(user=user).select_related('user')


def get_record_by_id(record_id, user, is_admin=False):
    """
    Retrieve a single record by ID.
    Admins can view any record; regular users only their own.
    Returns (record, error_message) tuple.
    """
    try:
        if is_admin:
            return FinancialRecord.objects.get(pk=record_id), None
        return FinancialRecord.objects.get(pk=record_id, user=user), None
    except FinancialRecord.DoesNotExist:
        return None, "Financial record not found."


def apply_filters(queryset, filters: dict):
    """
    Apply validated filter parameters to a queryset.

    Supported filters:
        date_from, date_to  — date range
        category            — exact category match (case-insensitive)
        type                — income or expense
        month + year        — restrict to a specific calendar month
    """
    if filters.get('date_from'):
        queryset = queryset.filter(date__gte=filters['date_from'])

    if filters.get('date_to'):
        queryset = queryset.filter(date__lte=filters['date_to'])

    if filters.get('category'):
        queryset = queryset.filter(category__iexact=filters['category'].strip())

    if filters.get('type'):
        queryset = queryset.filter(type=filters['type'])

    if filters.get('month') and filters.get('year'):
        queryset = queryset.filter(
            date__month=filters['month'],
            date__year=filters['year']
        )
    elif filters.get('year'):
        queryset = queryset.filter(date__year=filters['year'])

    return queryset


def create_record(user, validated_data: dict) -> FinancialRecord:
    """Create and persist a new financial record for a user."""
    return FinancialRecord.objects.create(user=user, **validated_data)


def update_record(record: FinancialRecord, validated_data: dict) -> FinancialRecord:
    """Apply partial updates to an existing record and save."""
    for field, value in validated_data.items():
        setattr(record, field, value)
    record.save()
    return record


def delete_record(record: FinancialRecord) -> None:
    """Delete a financial record from the database."""
    record.delete()
