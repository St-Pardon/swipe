

# 💳 Swipe — FinTech Payments & Wallet Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey.svg)](https://flask.palletsprojects.com/)

**Swipe** is a production-ready backend for digital wallets, card issuing, invoicing, and notifications. The service is built with **Flask**, secured with **JWT**, supports **TOTP 2FA**, integrates **Stripe** for payments, and ships with a polished Swagger UI plus a curated Postman collection.

---

## 📚 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Setup](#-setup)
- [Running the Application](#-running-the-application)
- [Live Demo](#-live-demo)
- [Docker](#-docker)
- [Environment Variables](#-environment-variables)
- [Database Migrations](#-database-migrations)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Tooling & Integrations](#-tooling--integrations)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 🚀 Features

- **Authentication & Security**: JWT auth, password reset emails, and full TOTP-based two-factor authentication with backup codes (`app/routes/auth.py`, `app/routes/two_factor_auth.py`).
- **Accounts & Wallets**: Multi-currency accounts, balance aggregation, FX rates with margin controls (`app/routes/account.py`).
- **Virtual Cards & Spending**: Card issuance, card funding, transaction history, Stripe payment method linking, and spending limits (`app/routes/card.py`, `app/routes/card_payments.py`).
- **Invoices & Payments**: Invoice lifecycle management, Stripe Checkout sessions, hosted payment redirects, and status tracking (`app/routes/invoice.py`, `app/routes/invoice_payments.py`, `app/routes/payment_redirects.py`).
- **Notifications**: In-app and email notifications, preference management, bulk broadcast tooling, and admin maintenance endpoints (`app/routes/notifications.py`, `app/routes/admin_notifications.py`).
- **Documentation & Testing Utilities**: Swagger UI served via `app/swagger.py`, Postman collection `Swipe.json`, and scripts for exercising 2FA and webhook flows.
- **Landing Experience**: Responsive marketing page at the root route highlighting the product (`app/routes/base_route.py`).

---

## 🏗️ Architecture

```
swipe/
├── app/
│   ├── __init__.py
│   ├── config/
│   ├── docs/               # Swagger resource declarations
│   ├── models/
│   ├── routes/
│   ├── schema/
│   ├── services/
│   ├── utils/
│   ├── extensions.py
│   └── swagger.py
├── migrations/
├── run.py                   # Dev/prod entry point (Flask vs Waitress)
├── requirements.txt
├── Swipe.json               # Postman collection
├── NOTIFICATION_SYSTEM.md   # Deep dive documentation
└── README.md
```

---

## ✅ Requirements

- Python 3.10+
- Virtualenv / Conda
- SQLite (default) or PostgreSQL for production
- Stripe test keys for payment flows

---

## ⚙️ Setup

- **Clone**
  ```bash
  git clone https://github.com/yourusername/swipe.git
  cd swipe
  ```

- **Create virtual environment**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

- **Install dependencies** (pinned in `requirements.txt`)
  ```bash
  pip install -r requirements.txt
  ```

- **Environment files**
  ```bash
  cp .env.example .env
  ```
  Populate `.env` using the variables listed below.

---

## 🏃 Running the Application

- **Development (Flask auto-reload)**
  ```bash
  source .venv/bin/activate
  export FLASK_ENV=development
  python run.py
  ```

- **Production-like (Waitress WSGI server)**
  ```bash
  source .venv/bin/activate
  export FLASK_ENV=production
  export HOST=0.0.0.0
  export PORT=8000
  python run.py
  ```
  Waitress is bundled via `waitress==3.0.2` after the dependency freeze.

Application default URL: `http://127.0.0.1:5000`

---

## 🌐 Live Demo

- **Landing Page**: https://swipe-bczl.onrender.com
- **Swagger Docs**: https://swipe-bczl.onrender.com/docs

This Render deployment mirrors the configuration described above and provides quick access to the marketing site and interactive API documentation.

---

## 🐳 Docker

- **Build & Run**
  ```bash
  docker compose up --build
  ```

- **Teardown**
  ```bash
  docker compose down
  ```

The Compose setup runs a single container (`swipe-web`) using SQLite for storage. On boot, `docker-entrypoint.sh` loads `.env`, applies `flask db upgrade`, and then launches the server via `run.py`.

> **Tip:** SQLite stores its database file inside the mounted project directory (default `swipe.db`). If you need a clean start, remove that file before restarting the container. To switch to Postgres later, add a database service to `docker-compose.yml` and set `DATABASE_URL` accordingly before `docker compose up`.

---

## 🔐 Environment Variables

| Key | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask secret key for sessions and JWT signing |
| `DATABASE_URL` | SQLAlchemy URI (`sqlite:///swipe.db` or PostgreSQL URI) |
| `JWT_SECRET_KEY` | JWT signing key (fallbacks to `SECRET_KEY` if omitted) |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` | Stripe integration |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS` | Email delivery |
| `NOTIFICATION_BROADCAST_LIMIT` | Safety guard for admin broadcasts |
| `FRONTEND_BASE_URL` | Used by payment redirect routes |
| `FX_API_KEY` | Optional foreign exchange API key |

Consult `.env.example` for the full list plus sensible defaults.

---

## 🗃️ Database Migrations

```bash
flask db upgrade

# Create new migration
flask db migrate -m "describe change"
flask db upgrade
```

Initial migrations live in `migrations/versions/`.

---

## 📘 API Documentation

- **Swagger UI**: visit `http://127.0.0.1:5000/docs/`
- **Namespaces**: Authentication, Accounts, Wallets, Transactions, Cards, 2FA, Invoices, Invoice Payments, Notifications, Admin Notifications.
- **Postman**: Import `Swipe.json` for preconfigured environments covering 2FA, invoice, payment, and webhook flows.

Helper scripts: `direct_2fa_test.py`, `test_endpoint.py`, `test_webhook.py` demonstrate common workflows.

---

## 🧪 Testing

```bash
source .venv/bin/activate
pytest
```

Targeted smoke scripts also live at the project root for manual verification.

---

## 🛠️ Tooling & Integrations

- **Flask ecosystem**: Flask, Flask-JWT-Extended, Flask-Migrate, Flask-SQLAlchemy, Flask-Mail, Flask-RESTX.
- **Data & Serialization**: Marshmallow, Marshmallow-SQLAlchemy.
- **Payments**: Stripe SDK, custom `PaymentService` (`app/services/payment_service.py`).
- **Notifications**: Email + in-app via `NotificationService` and `EmailService`.
- **Security**: Passlib for hashing, PyOTP for TOTP, quiet-hours aware notification settings.
- **Production**: Waitress WSGI server; configurable host/port via environment variables.

Pinned dependencies are maintained through `pip freeze` (see `requirements.txt`).

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit changes (`git commit -m "feat: add awesome thing"`)
4. Push and open a pull request

Please include tests and Swagger doc updates where relevant.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📬 Contact

- **Project Lead**: Onyedikachi Onu
- **Email**: [okc4pardon@gmail.com](mailto:okc4pardon@gmail.com)
- **GitHub**: [github.com/St-Pardon](https://github.com/St-Pardon)
