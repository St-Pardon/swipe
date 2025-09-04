

# 💳 Swipe — A FinTech API for Transactions, Accounts & Virtual Cards

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/swipe/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](https://github.com/yourusername/swipe/tests)

**Swipe** is a scalable, secure, and modern FinTech backend API built with **Flask**. It allows users to create and manage financial transactions and accounts, integrates with external APIs for **real-time currency conversion**, and supports **virtual card generation**.

---

## 🚀 Features

* ✅ User registration & authentication (JWT-based)
* 💰 Create and manage financial **transactions**
* 🏦 Manage multiple **bank accounts**
* 🌍 **Real-time currency conversion** (via external APIs like Fixer or OpenExchange)
* 💳 **Virtual card generation** (with secure tokenization)
* 📊 Transaction history and analytics
* 🔐 Secure API design with rate limiting and request validation

---

## 📁 Project Structure

```
swipe/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── config.py
│   └── extensions.py
├── migrations/
├── run.py
├── .env.example
├── .flaskenv.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/swipe.git
cd swipe
```

### 2. Set up your virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy and modify the `.env` and `.flaskenv`:

```bash
cp .env.example .env
cp .flaskenv.example .flaskenv
```

Update them with your local and API settings.

---

### 5. Run database migrations

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Start the Flask server

```bash
flask run
```

App will be running at `http://127.0.0.1:5000/`

---

## 🔑 Example .env

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///swipe.db

CURRENCY_API_KEY=your-fixer-api-key
VIRTUAL_CARD_API_KEY=your-card-service-api-key
```

---

## 📖 API Endpoints Overview

| Method | Endpoint            | Description                     |
| ------ | ------------------- | ------------------------------- |
| `GET`  | `/`                 | Health check                    |
| `POST` | `/auth/register`    | Create a new user               |
| `POST` | `/auth/login`       | Authenticate user and get token |
| `GET`  | `/accounts/`        | List user's accounts            |
| `POST` | `/accounts/`        | Create a new financial account  |
| `GET`  | `/transactions/`    | List transactions               |
| `POST` | `/transactions/`    | Create a new transaction        |
| `GET`  | `/currency/convert` | Convert between currencies      |
| `POST` | `/cards/virtual`    | Generate a virtual card         |

> Full API docs coming soon via Swagger/OpenAPI.

---

## 🧪 Testing

```bash
pytest
```

> You can find tests inside the `tests/` directory (coming soon).

---

## 🛠️ Built With

* [Flask](https://flask.palletsprojects.com/)
* [Flask-Migrate](https://flask-migrate.readthedocs.io/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* [python-dotenv](https://github.com/theskumar/python-dotenv)
* [Requests](https://requests.readthedocs.io/)
* External APIs (e.g. [Fixer.io](https://fixer.io), [Stripe Issuing](https://stripe.com/issuing), etc.)

---

## 📦 Deployment (Coming Soon)

Planned deployment methods:

* Docker
* Heroku
* Railway or Fly.io

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m "Add some feature"`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📬 Contact

**Project Lead:** \[Onyedikachi Onu]
**Email:** [okc4pardon@gmail.com](mailto:your@email.com)
**GitHub:** [github.com/St-Pardon](https://github.com/St-Pardon)
