"""
Serializers for the transactions app.
"""

from rest_framework import serializers
from .models import FinancialRecord
import datetime


class FinancialRecordSerializer(serializers.ModelSerializer):
    """Full read representation of a financial record."""

    owner = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            'id', 'owner', 'amount', 'type', 'category',
            'date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class FinancialRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new financial record.
    Enforces all validation rules before database write.
    """

    class Meta:
        model = FinancialRecord
        fields = ['amount', 'type', 'category', 'date', 'notes']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number greater than zero.")
        return value

    def validate_type(self, value):
        allowed = [t[0] for t in FinancialRecord.TransactionType.choices]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Invalid transaction type. Must be one of: {', '.join(allowed)}."
            )
        return value

    def validate_category(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category cannot be empty.")
        if len(value) > 100:
            raise serializers.ValidationError("Category must be 100 characters or fewer.")
        return value.lower()

    def validate_date(self, value):
        if not isinstance(value, datetime.date):
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        # Reject future dates more than 1 year ahead (reasonable guard)
        max_future = datetime.date.today().replace(year=datetime.date.today().year + 1)
        if value > max_future:
            raise serializers.ValidationError("Date cannot be more than 1 year in the future.")
        return value

    def create(self, validated_data):
        # user is injected by the view via perform_create
        return FinancialRecord.objects.create(**validated_data)


class FinancialRecordUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing financial record.
    All fields are optional (PATCH-style partial update supported).
    """

    class Meta:
        model = FinancialRecord
        fields = ['amount', 'category', 'date', 'notes']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number greater than zero.")
        return value

    def validate_category(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category cannot be empty.")
        return value.lower()

    def validate_date(self, value):
        if not isinstance(value, datetime.date):
            raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return value


class FilterParamsSerializer(serializers.Serializer):
    """
    Validates query parameters for filtering financial records.
    All filter fields are optional.
    """
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    category = serializers.CharField(required=False, max_length=100)
    type = serializers.ChoiceField(
        choices=FinancialRecord.TransactionType.choices,
        required=False
    )
    month = serializers.IntegerField(required=False, min_value=1, max_value=12)
    year = serializers.IntegerField(required=False, min_value=2000, max_value=2100)

    def validate(self, data):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "'date_from' must be earlier than or equal to 'date_to'."
            )
        return data
