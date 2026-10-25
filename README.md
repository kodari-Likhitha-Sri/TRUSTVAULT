# 🛡️ TrustVault - Secure Role-Based Document Management System

Welcome to **TrustVault**! TrustVault is an enterprise document security platform built with **Python**, **Flask**, **SQLAlchemy**, **Flask-Login**, **Flask-Bcrypt**, **Flask-WTF**, and **Bootstrap 5**. It enforces strict Role-Based Access Control (RBAC), multi-category file management, and immutable audit logging inside an affectionate, human-friendly user interface.

---

## 🚀 Quick Start (Running the Website)

### Option 1: One-Click Windows Batch Launcher (Easiest)
Simply double-click:
```cmd
run_trustvault.bat
```
*This script automatically initializes the database, seeds test data, launches Flask, and opens your default browser at `http://127.0.0.1:5000`.*

### Option 2: Python Browser Auto-Launcher
```bash
python launch.py
```
*Starts the server and automatically pops open `http://127.0.0.1:5000` in your web browser.*

### Option 3: Standard Terminal Execution
```bash
# 1. (Optional) Re-seed fresh demo data:
python seed_demo.py

# 2. Run the application:
python run.py
```
Visit **http://127.0.0.1:5000** in any browser.

---

## 🔑 Demo Accounts (Instant 1-Click Login)

The login screen features instant 1-click auto-fill buttons for all three roles:

| Role | Email | Password | Primary Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@trustvault.com` | `Admin@123` | System oversight, User Management (`/users`), role changes, immutable Activity Logs (`/logs`), delete users. |
| **Document Owner** | `owner@trustvault.com` | `Owner@123` | Upload files up to 20MB (`/upload`), delete own files, grant Read/Edit access (`/share`), revoke permissions anytime. |
| **Document Viewer** | `viewer@trustvault.com` | `Viewer@123` | Access only documents explicitly shared with them, download files, strict 403 protection on admin/upload routes. |
| **Secondary Owner** | `alex@trustvault.com` | `Alex@123` | Medical category owner with cross-team sharing. |

---

## 💖 Affectionate, Human-Centric UI Features

1. **Personalized Greetings**: Real-time morning, afternoon, and evening warm welcomes with caring daily affirmations.
2. **Atmosphere Theme Switcher**: 4 soothing color moods selectable directly from the top navigation bar:
   - 🌙 **Twilight Velvet** (Deep royal indigo & cyan)
   - 🌅 **Warm Sunset** (Cozy amber gold & sunset orange)
   - 🌹 **Rose Gold** (Gentle rose quartz & comforting warmth)
   - 🍃 **Serene Emerald** (Calming mint & cyber teal)
3. **VaultPal Assistant**: A friendly floating companion at the bottom-right corner offering instant guidance on permissions, security reassurance, and a *"Send Good Vibes"* confetti celebration button!
4. **Compassionate Empty States & Helper Bubbles**: Friendly tips explaining how RBAC works without technical intimidation.

---

## 📁 Project Structure

```
TrustVault/
├── frontend/                     # All Presentation Layer & User Interface Files
│   ├── static/                   # Static assets
│   │   ├── css/
│   │   │   └── style.css         # Dark luxury design system, themes & typography
│   │   ├── js/
│   │   │   └── main.js           # UI interactions, alerts, client-side behaviors
│   │   ├── images/avatars/       # User profile avatars
│   │   └── uploads/              # Stored document files (pdf, docs, ppt, images)
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── errors/               # 403, 404, 413 error pages
│   │   ├── base.html             # Main application shell with sidebar & topbar
│   │   ├── dashboard.html        # Metrics, KPI stats & activity overview
│   │   ├── documents.html        # Document library & categorization
│   │   ├── document_detail.html  # Document preview, version history & access control
│   │   ├── upload.html           # Document upload interface
│   │   ├── share.html            # Permission sharing management
│   │   ├── categories.html       # Category browser
│   │   ├── search.html           # Full-text & metadata search
│   │   ├── users.html            # Admin user management
│   │   ├── logs.html             # Audit trail & activity logs
│   │   ├── profile.html          # User profile & settings
│   │   ├── login.html            # Authentication login
│   │   └── register.html         # User registration
│   └── README.md
│
├── backend/                      # All Application Logic, Services & Database Files
│   ├── app/                      # Modular application controllers & services
│   │   ├── audit/                # Immutable activity & security audit logging
│   │   ├── auth/                 # Authentication & authorization routes
│   │   ├── dashboard/            # Dashboard data aggregation & analytics
│   │   ├── decorators/           # RBAC decorators (@role_required)
│   │   ├── documents/            # Document management, versioning & storage
│   │   ├── models/               # SQLAlchemy models (User, Document, Permission, Log)
│   │   ├── permissions/          # Granular access control logic
│   │   ├── repositories/         # Database persistence abstractions
│   │   ├── users/                # User management services
│   │   ├── utils/                # Security utilities & helpers
│   │   ├── forms.py              # Flask-WTF validation forms
│   │   └── __init__.py           # Flask app factory with frontend template resolver
│   ├── config.py                 # Configuration settings & environment paths
│   ├── run.py                    # Dedicated backend runner
│   ├── seed_demo.py              # Initial database seeder for demo accounts
│   ├── tests_trustvault.py       # Automated unit & integration tests
│   ├── trustvault.db             # SQLite database storage
│   ├── requirements.txt          # Backend dependencies
│   └── README.md
│
├── run.py                        # Project root launcher
├── launch.py                     # Auto-browser launcher
├── run_trustvault.bat            # Windows one-click batch launcher
├── requirements.txt              # Root dependency reference
└── README.md                     # Project documentation
```

---

## 🧪 Automated Unit Testing
Run the test suite from root or backend:
```bash
python tests_trustvault.py
```
*All 15 unit and integration tests verify authentication, owner uploads, viewer RBAC restrictions (403), versioning, and multi-field search.*
