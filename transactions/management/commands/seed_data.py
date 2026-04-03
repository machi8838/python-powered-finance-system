"""
Management command: seed_data

Creates sample users and financial records for testing.
Usage: python manage.py seed_data
"""

import random
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from users.models import UserProfile
from transactions.models import FinancialRecord


SAMPLE_INCOME = [
    ('salary', Decimal('50000.00')),
    ('salary', Decimal('52000.00')),
    ('freelance', Decimal('8000.00')),
    ('freelance', Decimal('3500.00')),
    ('investment', Decimal('1200.00')),
    ('investment', Decimal('950.00')),
    ('rental', Decimal('15000.00')),
    ('bonus', Decimal('10000.00')),
    ('gift', Decimal('2000.00')),
]

SAMPLE_EXPENSES = [
    ('food', Decimal('3500.00')),
    ('food', Decimal('2800.00')),
    ('food', Decimal('1200.00')),
    ('rent', Decimal('12000.00')),
    ('rent', Decimal('12000.00')),
    ('utilities', Decimal('1800.00')),
    ('utilities', Decimal('2200.00')),
    ('travel', Decimal('5000.00')),
    ('travel', Decimal('8000.00')),
    ('healthcare', Decimal('3000.00')),
    ('entertainment', Decimal('1500.00')),
    ('education', Decimal('4500.00')),
    ('shopping', Decimal('6000.00')),
    ('transport', Decimal('2000.00')),
]


class Command(BaseCommand):
    help = 'Seeds the database with sample users and financial records for testing.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        self._create_users()
        self._create_transactions()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self._print_summary()

    def _create_users(self):
        users = [
            ('admin_user', 'admin@finance.com', 'Admin@1234', UserProfile.Role.ADMIN),
            ('analyst_user', 'analyst@finance.com', 'Analyst@1234', UserProfile.Role.ANALYST),
            ('viewer_user', 'viewer@finance.com', 'Viewer@1234', UserProfile.Role.VIEWER),
        ]
        for username, email, password, role in users:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password)
                UserProfile.objects.create(user=user, role=role)
                self.stdout.write(f'  Created user: {username} ({role})')
            else:
                self.stdout.write(f'  Skipped existing user: {username}')

    def _create_transactions(self):
        try:
            user = User.objects.get(username='admin_user')
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('admin_user not found, skipping transactions.'))
            return

        if FinancialRecord.objects.filter(user=user).exists():
            self.stdout.write('  Transactions already exist — skipping.')
            return

        today = date.today()
        records = []

        for i, (category, amount) in enumerate(SAMPLE_INCOME):
            offset = random.randint(0, 180)
            records.append(FinancialRecord(
                user=user,
                amount=amount,
                type=FinancialRecord.TransactionType.INCOME,
                category=category,
                date=today - timedelta(days=offset),
                notes=f'Sample income: {category}',
            ))

        for i, (category, amount) in enumerate(SAMPLE_EXPENSES):
            offset = random.randint(0, 180)
            records.append(FinancialRecord(
                user=user,
                amount=amount,
                type=FinancialRecord.TransactionType.EXPENSE,
                category=category,
                date=today - timedelta(days=offset),
                notes=f'Sample expense: {category}',
            ))

        FinancialRecord.objects.bulk_create(records)
        self.stdout.write(f'  Created {len(records)} financial records for admin_user.')

    def _print_summary(self):
        self.stdout.write('\n--- Test Credentials ---')
        self.stdout.write('Admin:   admin_user   / Admin@1234')
        self.stdout.write('Analyst: analyst_user / Analyst@1234')
        self.stdout.write('Viewer:  viewer_user  / Viewer@1234')
        self.stdout.write('------------------------\n')
