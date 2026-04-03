# Finance Tracking System — Backend

A production-ready Django + SQLite backend for personal finance management.
Supports full CRUD on financial records, role-based access control, and analytics.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 |
| API | Django REST Framework |
| Database | SQLite (via Django ORM) |
| Auth | Django session authentication |
| Language | Python 3.10+ |

**Why SQLite?** SQLite is the default Django database, requires zero configuration, and is
ideal for a single-user or small-team finance tool. It stores the entire database as one
file (`db.sqlite3`), making backup and portability trivial. For a multi-user or production
deployment, swapping to PostgreSQL requires only a settings change.

---

## Project Structure

```
finance_project/
│
├── manage.py                        # Django entry point
├── requirements.txt
├── README.md
│
├── finance_project/                 # Django project config
│   ├── settings.py
│   ├── urls.py                      # Root URL router
│   └── wsgi.py
│
├── users/                           # User management app
│   ├── models.py                    # UserProfile (role extension)
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py               # Custom role-based permission classes
│   └── admin.py
│
├── transactions/                    # Financial records app
│   ├── models.py                    # FinancialRecord model
│   ├── serializers.py               # Create / Update / Filter serializers
│   ├── views.py
│   ├── urls.py
│   ├── tests.py                     # Full test suite
│   └── management/
│       └── commands/
│           └── seed_data.py         # Sample data loader
│
├── analytics/                       # Summary & insights app
│   ├── views.py
│   └── urls.py
│
└── services/                        # Business logic layer (no HTTP)
    ├── transaction_service.py
    └── analytics_service.py
```

---

## Setup Instructions

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd finance_project
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
python manage.py makemigrations users transactions
python manage.py migrate
```

### 4. Create a superuser (for Django Admin)

```bash
python manage.py createsuperuser
```

> **Note:** The superuser will not automatically get a `UserProfile`. Log into
> `/admin/` and create one manually, or use the `seed_data` command below.

### 5. Seed sample data (optional)

```bash
python manage.py seed_data
```

This creates three users with pre-set credentials and ~23 sample transactions.

### 6. Run the development server

```bash
python manage.py runserver
```

Server runs at `http://127.0.0.1:8000/`.

### 7. Run tests

```bash
python manage.py test transactions
```

---

## User Roles

| Role | View Transactions | Filter/Analytics | Create/Update/Delete | Manage Users |
|---|:---:|:---:|:---:|:---:|
| **Viewer** | ✅ | ❌ | ❌ | ❌ |
| **Analyst** | ✅ | ✅ | ❌ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |

Roles are stored on the `UserProfile` model as a `CharField` with choices.

---

## API Reference

All endpoints are prefixed with `/api/`.
Authentication uses Django sessions — log in first via `POST /api/users/login/`.

### Authentication

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/users/login/` | Log in | Public |
| `POST` | `/api/users/logout/` | Log out | Authenticated |
| `GET` | `/api/users/me/` | Current user profile | Authenticated |

**Login body:**
```json
{ "username": "admin_user", "password": "Admin@1234" }
```

---

### Users

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/users/` | List all users | Admin |
| `POST` | `/api/users/create/` | Create a new user | Admin |
| `GET` | `/api/users/<id>/` | Get user detail | Admin or own profile |
| `PUT` | `/api/users/<id>/` | Update user / change role | Admin |
| `DELETE` | `/api/users/<id>/` | Delete a user | Admin |

**Create user body:**
```json
{
  "username": "jane",
  "email": "jane@example.com",
  "password": "SecurePass1",
  "role": "analyst"
}
```

---

### Transactions

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/transactions/` | List user's transactions | All authenticated |
| `POST` | `/api/transactions/` | Create a transaction | Admin |
| `GET` | `/api/transactions/<id>/` | Get single transaction | All authenticated |
| `PUT` | `/api/transactions/<id>/` | Full update | Admin |
| `PATCH` | `/api/transactions/<id>/` | Partial update | Admin |
| `DELETE` | `/api/transactions/<id>/` | Delete transaction | Admin |
| `GET` | `/api/transactions/filter/` | Filter transactions | All authenticated |

**Create transaction body:**
```json
{
  "amount": "5000.00",
  "type": "income",
  "category": "salary",
  "date": "2024-03-01",
  "notes": "March salary"
}
```

**Filter query parameters:**

| Param | Type | Example |
|---|---|---|
| `type` | `income` or `expense` | `?type=expense` |
| `category` | string | `?category=food` |
| `date_from` | `YYYY-MM-DD` | `?date_from=2024-01-01` |
| `date_to` | `YYYY-MM-DD` | `?date_to=2024-03-31` |
| `month` | integer 1–12 | `?month=3&year=2024` |
| `year` | integer | `?year=2024` |

All parameters are optional and combinable.

---

### Analytics / Summary

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/summary/` | Full summary (income, expenses, balance, categories) | Analyst, Admin |
| `GET` | `/api/summary/monthly/` | Monthly aggregated totals | Analyst, Admin |
| `GET` | `/api/summary/income/` | Total income | Analyst, Admin |
| `GET` | `/api/summary/expenses/` | Total expenses | Analyst, Admin |
| `GET` | `/api/summary/balance/` | Current balance | Analyst, Admin |
| `GET` | `/api/summary/recent/?limit=10` | Recent transactions | All authenticated |

**Sample `/api/summary/` response:**
```json
{
  "total_income": "142500.00",
  "total_expenses": "49500.00",
  "current_balance": "93000.00",
  "category_breakdown": [
    { "category": "food", "type": "expense", "total": "7500.00", "count": 3 },
    { "category": "salary", "type": "income", "total": "102000.00", "count": 2 }
  ]
}
```

---

## Validation Rules

| Field | Rule |
|---|---|
| `amount` | Must be a positive number > 0 |
| `type` | Must be exactly `income` or `expense` |
| `category` | Required, non-empty, max 100 chars |
| `date` | Valid date, not more than 1 year in the future |
| `filter date_from/date_to` | `date_from` must not be after `date_to` |
| `limit` (recent activity) | Integer between 1 and 50 |

All validation is enforced in serializers **before** any database write.
The application will never crash on invalid user input.

---

## Error Responses

All error responses follow this shape:

```json
{ "error": "Human-readable message." }
```

or for field-level validation failures:

```json
{
  "errors": {
    "amount": ["Amount must be a positive number greater than zero."],
    "type": ["Invalid transaction type. Must be one of: income, expense."]
  }
}
```

| Scenario | HTTP Status |
|---|---|
| Not authenticated | 403 Forbidden |
| Insufficient role | 403 Forbidden |
| Resource not found | 404 Not Found |
| Invalid input | 400 Bad Request |
| Login failure | 401 Unauthorized |
| Success (create) | 201 Created |
| Success (other) | 200 OK |

---

## Design Assumptions

1. **Personal finance only.** Each user sees only their own transactions. Admins can view all records.
2. **Categories are free text.** No predefined category list — stored and compared case-insensitively.
3. **Authentication is session-based** using Django's built-in system. Token/JWT auth can be added via DRF's `TokenAuthentication`.
4. **Amounts use Decimal** (not float) to avoid floating-point rounding errors in financial calculations.
5. **SQLite is the persistence layer.** Swap to PostgreSQL by editing `DATABASES` in `settings.py`.
6. **Seeded admin can create transactions for themselves only.** There is no concept of creating records on behalf of another user.

---

## Django Admin

Available at `/admin/` after creating a superuser.

Registered admin panels:
- **UserProfile** — view and edit user roles
- **FinancialRecord** — full CRUD with filters by type, category, and date

---

## Running Tests

```bash
# All tests
python manage.py test transactions

# Verbose output
python manage.py test transactions --verbosity=2
```

Test coverage includes:
- Model creation and ordering
- Serializer validation (valid and invalid inputs)
- Service layer logic (filtering, aggregation)
- API permission checks per role
- End-to-end create / update / delete flows
