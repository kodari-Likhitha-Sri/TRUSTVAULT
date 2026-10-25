# TrustVault Frontend

This directory contains the user interface components, styles, interactive scripts, and templates for the TrustVault platform.

## Directory Structure

```
frontend/
├── static/
│   ├── css/
│   │   └── style.css          # Core design system (dark mode, glassmorphism, responsive grid)
│   ├── js/
│   │   └── main.js            # UI interactions, auto-dismiss alerts, password toggles, modal helpers
│   ├── images/
│   │   └── avatars/           # User profile avatars
│   └── uploads/               # Uploaded files (PDFs, DOCX, PPT, Images)
└── templates/
    ├── errors/                # HTTP error pages (403, 404, 413)
    ├── base.html              # Base shell layout (sidebar, topbar, modals)
    ├── dashboard.html         # Main overview, KPI cards, recent documents
    ├── documents.html         # Document repository, filtering & views
    ├── document_detail.html   # File preview, version history, access list
    ├── document_edit.html     # Metadata editor
    ├── upload.html            # Multi-format document uploader
    ├── share.html             # Access control & permission management
    ├── categories.html        # Category browser
    ├── search.html            # Global search interface
    ├── users.html             # Administrator user management
    ├── logs.html              # Immutable audit trail
    ├── profile.html           # User settings & security
    ├── login.html             # Authentication login screen
    ├── register.html          # New account registration
    └── index.html             # Welcome landing page
```
