"""
Unit tests for the Finance Tracking System.

Tests cover:
  - Model validation
  - Serializer validation
  - Service layer logic
  - API endpoint behavior and permissions
"""

from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import UserProfile
from transactions.models import FinancialRecord
from transactions.serializers import FinancialRecordCreateSerializer
from services import transaction_service, analytics_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username, role=UserProfile.Role.VIEWER, password='TestPass@1'):
    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.create(user=user, role=role)
    return user


def make_record(user, amount='1000.00', type_='income', category='salary', days_ago=0):
    return FinancialRecord.objects.create(
        user=user,
        amount=Decimal(amount),
        type=type_,
        category=category,
        date=date.today() - timedelta(days=days_ago),
        notes='Test record',
    )


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------

class FinancialRecordModelTest(TestCase):

    def setUp(self):
        self.user = make_user('testuser')

    def test_str_representation(self):
        record = make_record(self.user)
        self.assertIn('testuser', str(record))
        self.assertIn('income', str(record))

    def test_default_ordering_is_by_date_desc(self):
        make_record(self.user, days_ago=10)
        make_record(self.user, days_ago=0)
        records = list(FinancialRecord.objects.filter(user=self.user))
        self.assertTrue(records[0].date >= records[1].date)

    def test_amount_stored_as_decimal(self):
        record = make_record(self.user, amount='1234.56')
        self.assertEqual(record.amount, Decimal('1234.56'))


# ---------------------------------------------------------------------------
# Serializer Validation Tests
# ---------------------------------------------------------------------------

class FinancialRecordCreateSerializerTest(TestCase):

    def _serialize(self, data):
        return FinancialRecordCreateSerializer(data=data)

    def test_valid_income_record(self):
        s = self._serialize({
            'amount': '500.00', 'type': 'income',
            'category': 'salary', 'date': str(date.today())
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_rejects_zero_amount(self):
        s = self._serialize({
            'amount': '0.00', 'type': 'income',
            'category': 'salary', 'date': str(date.today())
        })
        self.assertFalse(s.is_valid())
        self.assertIn('amount', s.errors)

    def test_rejects_negative_amount(self):
        s = self._serialize({
            'amount': '-100.00', 'type': 'income',
            'category': 'salary', 'date': str(date.today())
        })
        self.assertFalse(s.is_valid())
        self.assertIn('amount', s.errors)

    def test_rejects_invalid_type(self):
        s = self._serialize({
            'amount': '100.00', 'type': 'transfer',
            'category': 'salary', 'date': str(date.today())
        })
        self.assertFalse(s.is_valid())
        self.assertIn('type', s.errors)

    def test_rejects_empty_category(self):
        s = self._serialize({
            'amount': '100.00', 'type': 'income',
            'category': '   ', 'date': str(date.today())
        })
        self.assertFalse(s.is_valid())
        self.assertIn('category', s.errors)

    def test_category_is_lowercased(self):
        s = self._serialize({
            'amount': '100.00', 'type': 'income',
            'category': 'SALARY', 'date': str(date.today())
        })
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['category'], 'salary')

    def test_rejects_missing_required_fields(self):
        s = self._serialize({'amount': '100.00'})
        self.assertFalse(s.is_valid())
        self.assertIn('type', s.errors)
        self.assertIn('category', s.errors)
        self.assertIn('date', s.errors)


# ---------------------------------------------------------------------------
# Service Layer Tests
# ---------------------------------------------------------------------------

class TransactionServiceTest(TestCase):

    def setUp(self):
        self.user = make_user('svcuser', role=UserProfile.Role.ADMIN)
        make_record(self.user, amount='5000.00', type_='income', category='salary')
        make_record(self.user, amount='1000.00', type_='expense', category='food')
        make_record(self.user, amount='500.00', type_='expense', category='transport')

    def test_get_user_records_returns_only_own_records(self):
        other = make_user('other')
        make_record(other, amount='999.00')
        records = transaction_service.get_user_records(self.user)
        self.assertEqual(records.count(), 3)

    def test_apply_filters_by_type(self):
        records = transaction_service.get_user_records(self.user)
        filtered = transaction_service.apply_filters(records, {'type': 'expense'})
        self.assertEqual(filtered.count(), 2)

    def test_apply_filters_by_category(self):
        records = transaction_service.get_user_records(self.user)
        filtered = transaction_service.apply_filters(records, {'category': 'food'})
        self.assertEqual(filtered.count(), 1)

    def test_apply_filters_by_date_range(self):
        records = transaction_service.get_user_records(self.user)
        filtered = transaction_service.apply_filters(records, {
            'date_from': date.today(),
            'date_to': date.today(),
        })
        self.assertEqual(filtered.count(), 3)

    def test_get_record_by_id_own_record(self):
        record = FinancialRecord.objects.filter(user=self.user).first()
        found, err = transaction_service.get_record_by_id(record.pk, self.user)
        self.assertIsNotNone(found)
        self.assertIsNone(err)

    def test_get_record_by_id_not_found(self):
        found, err = transaction_service.get_record_by_id(99999, self.user)
        self.assertIsNone(found)
        self.assertIsNotNone(err)


class AnalyticsServiceTest(TestCase):

    def setUp(self):
        self.user = make_user('analytic_user', role=UserProfile.Role.ANALYST)
        make_record(self.user, amount='10000.00', type_='income', category='salary')
        make_record(self.user, amount='2000.00', type_='income', category='freelance')
        make_record(self.user, amount='3000.00', type_='expense', category='rent')
        make_record(self.user, amount='500.00', type_='expense', category='food')

    def test_total_income(self):
        self.assertEqual(analytics_service.get_total_income(self.user), Decimal('12000.00'))

    def test_total_expenses(self):
        self.assertEqual(analytics_service.get_total_expenses(self.user), Decimal('3500.00'))

    def test_current_balance(self):
        self.assertEqual(analytics_service.get_current_balance(self.user), Decimal('8500.00'))

    def test_category_breakdown_has_correct_categories(self):
        breakdown = analytics_service.get_category_breakdown(self.user)
        categories = {row['category'] for row in breakdown}
        self.assertIn('salary', categories)
        self.assertIn('rent', categories)

    def test_recent_activity_respects_limit(self):
        records = analytics_service.get_recent_activity(self.user, limit=2)
        self.assertEqual(len(records), 2)


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TransactionAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user('api_admin', role=UserProfile.Role.ADMIN)
        self.viewer = make_user('api_viewer', role=UserProfile.Role.VIEWER)
        self.analyst = make_user('api_analyst', role=UserProfile.Role.ANALYST)
        make_record(self.admin, amount='5000.00', type_='income', category='salary')

    def _login(self, user):
        self.client.force_authenticate(user=user)

    def test_list_transactions_authenticated(self):
        self._login(self.admin)
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transactions', response.data)

    def test_list_transactions_unauthenticated(self):
        response = self.client.get('/api/transactions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_transaction_as_admin(self):
        self._login(self.admin)
        data = {
            'amount': '1500.00',
            'type': 'expense',
            'category': 'rent',
            'date': str(date.today()),
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_transaction_as_viewer_is_forbidden(self):
        self._login(self.viewer)
        data = {
            'amount': '1500.00',
            'type': 'expense',
            'category': 'rent',
            'date': str(date.today()),
        }
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_transaction_invalid_data(self):
        self._login(self.admin)
        data = {'amount': '-500.00', 'type': 'unknown', 'category': '', 'date': 'bad-date'}
        response = self.client.post('/api/transactions/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_delete_transaction_as_admin(self):
        self._login(self.admin)
        record = FinancialRecord.objects.filter(user=self.admin).first()
        response = self.client.delete(f'/api/transactions/{record.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_transaction_as_viewer_is_forbidden(self):
        self._login(self.viewer)
        record = FinancialRecord.objects.filter(user=self.admin).first()
        response = self.client.delete(f'/api/transactions/{record.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_type(self):
        self._login(self.admin)
        response = self.client.get('/api/transactions/filter/?type=income')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for tx in response.data['transactions']:
            self.assertEqual(tx['type'], 'income')

    def test_filter_with_invalid_params(self):
        self._login(self.admin)
        response = self.client.get('/api/transactions/filter/?type=invalid_type')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SummaryAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = make_user('sum_admin', role=UserProfile.Role.ADMIN)
        self.analyst = make_user('sum_analyst', role=UserProfile.Role.ANALYST)
        self.viewer = make_user('sum_viewer', role=UserProfile.Role.VIEWER)
        make_record(self.admin, amount='10000.00', type_='income', category='salary')
        make_record(self.admin, amount='2000.00', type_='expense', category='food')

    def test_summary_accessible_by_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_income', response.data)
        self.assertIn('total_expenses', response.data)
        self.assertIn('current_balance', response.data)

    def test_summary_accessible_by_analyst(self):
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get('/api/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_summary_forbidden_for_viewer(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get('/api/summary/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_monthly_summary_structure(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/summary/monthly/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('monthly_summary', response.data)

    def test_recent_activity_accessible_to_all(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get('/api/summary/recent/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
