# Python-Powered Finance Tracking System

A clean, production-ready backend finance management system built with Django and SQLite.
Designed to manage personal financial transactions, generate summaries, and enforce role-based access control.

## Live Repository
https://github.com/machi8838/python-powered-finance-system

## Technology Stack
- **Framework:** Django 5.2
- **API:** Django REST Framework
- **Database:** SQLite (Django ORM)
- **Language:** Python 3.14
- **Authentication:** Django Session Authentication

## Why SQLite?
SQLite requires zero configuration, stores everything in a single file, and is perfectly
suited for a personal finance tracking system. Switching to PostgreSQL requires only
a one-line change in settings.py.

## Project Structure
finance_project/
├── users/            # User management + role-based permissions
├── transactions/     # Financial records CRUD + filtering
├── analytics/        # Summary and insights endpoints
├── services/         # Pure business logic layer
└── finance_project/  # Django config and settings
## User Roles
| Role | View | Filter/Analytics | Create/Update/Delete | Manage Users |
|---|:---:|:---:|:---:|:---:|
| Viewer | ✅ | ❌ | ❌ | ❌ |
| Analyst | ✅ | ✅ | ❌ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ |

## Setup Instructions
```bash
# 1. Clone the repository
git clone https://github.com/machi8838/python-powered-finance-system.git
cd python-powered-finance-system

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Load sample data
python manage.py seed_data

# 6. Start server
python manage.py runserver
```

## Test Credentials
| Role | Username | Password |
|---|---|---|
| Admin | admin_user | Admin@1234 |
| Analyst | analyst_user | Analyst@1234 |
| Viewer | viewer_user | Viewer@1234 |

## API Endpoints
| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | /api/users/login/ | Login | Public |
| GET | /api/transactions/ | List transactions | All |
| POST | /api/transactions/ | Create transaction | Admin |
| GET | /api/transactions/filter/ | Filter transactions | All |
| GET | /api/summary/ | Full financial summary | Analyst, Admin |
| GET | /api/summary/monthly/ | Monthly totals | Analyst, Admin |
| GET | /api/summary/balance/ | Current balance | Analyst, Admin |
| GET | /api/summary/recent/ | Recent activity | All |

## Assumptions
- Each user manages their own finances only
- Categories are free text stored in lowercase
- Authentication uses Django sessions
- Amounts use Decimal type for financial precision

## Running Tests
```bash
python manage.py test transactions --verbosity=2
```

## Django Admin Panel
http://127.0.0.1:8000/admin/
Login with admin_user / Admin@1234
