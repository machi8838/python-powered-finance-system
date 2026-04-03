"""
Transactions app models.

Defines the FinancialRecord model representing individual income/expense entries.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class FinancialRecord(models.Model):
    """
    Represents a single financial transaction (income or expense).

    Each record is owned by a user and belongs to a category.
    Amounts are stored as Decimal for precision.
    """

    class TransactionType(models.TextChoices):
        INCOME = 'income', 'Income'
        EXPENSE = 'expense', 'Expense'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='financial_records',
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transaction amount (must be positive)"
    )
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        db_index=True
    )
    category = models.CharField(
        max_length=100,
        db_index=True,
        help_text="e.g., food, salary, rent, travel"
    )
    date = models.DateField(
        db_index=True,
        help_text="Date of the transaction"
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Optional additional description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Financial Record'
        verbose_name_plural = 'Financial Records'
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.user.username} | {self.type} | {self.amount} | {self.date}"
