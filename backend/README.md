# TrustVault Backend

This directory houses the Python application server, database models, repository abstractions, business logic services, blueprint controllers, and configuration for TrustVault.

## Directory Structure

```
backend/
├── app/
│   ├── audit/                 # Audit logging routes and services
│   ├── auth/                  # Authentication, login, logout, registration
│   ├── dashboard/             # Dashboard metrics and recent document stats
│   ├── decorators/            # Role-based access control decorators (@role_required)
│   ├── documents/             # Document upload, versioning, download, preview
│   ├── models/                # SQLAlchemy database models (User, Document, Permission, etc.)
│   ├── permissions/           # RBAC permission sharing & revocation
│   ├── repositories/          # Clean database access abstractions
│   ├── users/                 # User management & profile controllers
│   ├── utils/                 # Security utilities & device/browser detection
│   ├── forms.py               # Flask-WTF validation forms
│   └── __init__.py            # Flask application factory with frontend template resolution
├── config.py                  # Application settings & environment paths
├── run.py                     # Backend server entry point
├── seed_demo.py               # Database seeder for demo accounts
├── tests_trustvault.py        # Automated test suite (15 unit & integration tests)
├── trustvault.db              # SQLite database storage
└── requirements.txt           # Python dependency specifications
```

## Running Backend

You can run the backend server directly from this folder:

```bash
cd backend
python run.py
```

Or run the test suite:

```bash
cd backend
python -m unittest tests_trustvault.py
```
