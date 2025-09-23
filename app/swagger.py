from flask_restx import Api
from flask import Blueprint

# Create a blueprint for Swagger
swagger_bp = Blueprint('swagger', __name__)

# Initialize Flask-RESTX API
api = Api(
    swagger_bp,
    version='1.0',
    title='Swipe Payment API',
    description="""
A comprehensive payment gateway API for virtual cards, wallets, and transfers.

## Features
- **Authentication**: JWT-based user authentication with registration, login, logout, password reset
- **User Management**: Complete user profile management and beneficiary handling  
- **Account Management**: Bank account creation, management, and balance tracking
- **Virtual Cards**: Create and manage virtual debit cards with Stripe integration
- **Wallet Operations**: Fund wallets using virtual cards with real-time balance updates
- **Transfer System**: Support for multiple transfer types (internal, beneficiary, customer, external)
- **Transaction History**: Complete audit trail of all financial operations
- **Webhook Integration**: Real-time Stripe webhook handling for payment status updates

## Transfer Types
- **Internal**: Transfer between user's own accounts
- **Beneficiary**: Transfer to saved beneficiaries
- **Customer**: Transfer to other Swipe users by email
- **External**: Transfer to external bank accounts (non-customers)

## Development Mode
When Stripe API keys are not configured, the system operates in development mode with:
- Mock payment processing
- Immediate balance updates
- Simulated payment intents and payouts
- Test-friendly unique IDs

## Authentication
Most endpoints require JWT authentication. Include the token in requests as:
`Authorization: Bearer {your_jwt_token}`

Obtain tokens via the `/auth/login` or `/auth/register` endpoints.
""",
    doc='/docs/',
    prefix='/api/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    },
    security='Bearer'
)

# Define namespaces for different API sections
auth_ns = api.namespace('auth', description='Authentication operations')
accounts_ns = api.namespace('accounts', description='Account management operations')
users_ns = api.namespace('users', description='User management operations')
cards_ns = api.namespace('cards', description='Virtual card operations')
wallets_ns = api.namespace('wallets', description='Wallet and transfer operations')
transactions_ns = api.namespace('transactions', description='Transaction history operations')
webhooks_ns = api.namespace('webhooks', description='Webhook handling operations')
invoices_ns = api.namespace('invoices', description='Invoice management operations')
invoice_payments_ns = api.namespace('invoice-payments', description='Invoice payment processing operations')

# Import documentation classes to register them
from app.docs.auth_docs import *
from app.docs.wallet_docs import *
from app.docs.accounts_docs import *
from app.docs.users_docs import *
from app.docs.cards_docs import *
from app.docs.transactions_docs import *
from app.docs.webhooks_docs import *
from app.docs.two_factor_auth_docs import *
from app.docs.invoice_docs import *
from app.docs.invoice_payments_docs import *
