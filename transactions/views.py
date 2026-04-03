"""
Views for the transactions app.

Handles CRUD operations for financial records with role-based access control.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import CanModifyRecords
from services import transaction_service
from .models import FinancialRecord
from .serializers import (
    FinancialRecordSerializer,
    FinancialRecordCreateSerializer,
    FinancialRecordUpdateSerializer,
    FilterParamsSerializer,
)


def _is_admin(user):
    try:
        return user.profile.is_admin
    except Exception:
        return False


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, CanModifyRecords])
def transaction_list(request):
    """
    GET  /api/transactions/  — List all transactions for the current user
    POST /api/transactions/  — Create a new transaction (Admin only)
    """
    if request.method == 'GET':
        records = transaction_service.get_user_records(request.user)
        serializer = FinancialRecordSerializer(records, many=True)
        return Response({
            'count': records.count(),
            'transactions': serializer.data
        })

    # POST — Admin only (enforced by CanModifyRecords)
    serializer = FinancialRecordCreateSerializer(data=request.data)
    if serializer.is_valid():
        record = transaction_service.create_record(request.user, serializer.validated_data)
        return Response(
            {
                'message': 'Transaction created successfully.',
                'transaction': FinancialRecordSerializer(record).data
            },
            status=status.HTTP_201_CREATED
        )
    return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, CanModifyRecords])
def transaction_detail(request, transaction_id):
    """
    GET    /api/transactions/<id>/  — View a single transaction
    PUT    /api/transactions/<id>/  — Full update (Admin only)
    PATCH  /api/transactions/<id>/  — Partial update (Admin only)
    DELETE /api/transactions/<id>/  — Delete (Admin only)
    """
    record, error = transaction_service.get_record_by_id(
        transaction_id, request.user, is_admin=_is_admin(request.user)
    )
    if error:
        return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(FinancialRecordSerializer(record).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = FinancialRecordUpdateSerializer(record, data=request.data, partial=partial)
        if serializer.is_valid():
            updated = transaction_service.update_record(record, serializer.validated_data)
            return Response({
                'message': 'Transaction updated successfully.',
                'transaction': FinancialRecordSerializer(updated).data
            })
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        transaction_service.delete_record(record)
        return Response(
            {'message': f'Transaction {transaction_id} deleted successfully.'},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_filter(request):
    """
    GET /api/transactions/filter/

    Filter transactions using query parameters:
        date_from=YYYY-MM-DD
        date_to=YYYY-MM-DD
        category=food
        type=income|expense
        month=1-12
        year=YYYY

    All parameters are optional and combinable.
    """
    param_serializer = FilterParamsSerializer(data=request.query_params)
    if not param_serializer.is_valid():
        return Response(
            {'errors': param_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    records = transaction_service.get_user_records(request.user)
    records = transaction_service.apply_filters(records, param_serializer.validated_data)

    serializer = FinancialRecordSerializer(records, many=True)
    return Response({
        'count': records.count(),
        'filters_applied': param_serializer.validated_data,
        'transactions': serializer.data
    })
