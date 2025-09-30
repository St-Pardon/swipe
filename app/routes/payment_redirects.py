from datetime import datetime

from flask import Blueprint, request, render_template_string

from app.extensions import db
from app.models.invoice_model import Invoice
from app.models.payment_intent_model import PaymentIntent

payment_redirects_bp = Blueprint("payment_redirects", __name__)

_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Payment Successful</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f7f7fb; color: #1f1f3d; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .card { background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(79, 70, 229, 0.25); max-width: 560px; text-align: center; }
        h1 { font-size: 2rem; margin-bottom: 1rem; color: #4f46e5; }
        p { margin-bottom: 0.75rem; }
        a { display: inline-block; margin-top: 1.5rem; padding: 0.75rem 1.75rem; border-radius: 999px; background: #4f46e5; color: white; text-decoration: none; font-weight: 600; }
        a:hover { background: #4338ca; }
        .meta { font-size: 0.9rem; color: #4b5563; }
    </style>
</head>
<body>
    <section class="card">
        <h1>Payment Successful</h1>
        <p>Your invoice payment has been recorded successfully.</p>
        {% if session_id %}<p class="meta">Session ID: {{ session_id }}</p>{% endif %}
        {% if invoice_id %}<p class="meta">Invoice ID: {{ invoice_id }}</p>{% endif %}
        <a href="/">Return to Dashboard</a>
    </section>
</body>
</html>
"""

_CANCEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Payment Cancelled</title>
    <style>
        body { font-family: Arial, sans-serif; background: #fff7f7; color: #3b0d0c; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .card { background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(220, 38, 38, 0.25); max-width: 560px; text-align: center; }
        h1 { font-size: 2rem; margin-bottom: 1rem; color: #dc2626; }
        p { margin-bottom: 0.75rem; }
        a { display: inline-block; margin-top: 1.5rem; padding: 0.75rem 1.75rem; border-radius: 999px; background: #dc2626; color: white; text-decoration: none; font-weight: 600; }
        a:hover { background: #b91c1c; }
        .meta { font-size: 0.9rem; color: #7f1d1d; }
    </style>
</head>
<body>
    <section class="card">
        <h1>Payment Cancelled</h1>
        <p>The invoice payment was cancelled. You can retry the payment anytime.</p>
        {% if session_id %}<p class="meta">Session ID: {{ session_id }}</p>{% endif %}
        {% if invoice_id %}<p class="meta">Invoice ID: {{ invoice_id }}</p>{% endif %}
        <a href="/">Return to Dashboard</a>
    </section>
</body>
</html>
"""


@payment_redirects_bp.route("/payment/success")
def payment_success():
    session_id = request.args.get("session_id")
    invoice_id = None

    if session_id:
        payment_intent = PaymentIntent.query.filter_by(client_secret=session_id).first()
        if payment_intent:
            invoice_id = str(payment_intent.invoice_id) if payment_intent.invoice_id else None

            if payment_intent.status != "succeeded":
                payment_intent.status = "succeeded"
                payment_intent.confirmed_at = datetime.utcnow()

                invoice = payment_intent.invoice or Invoice.query.get(payment_intent.invoice_id)
                if invoice:
                    if hasattr(invoice, "payment_status"):
                        invoice.payment_status = "paid"
                    if hasattr(invoice, "status") and getattr(invoice, "status") != "paid":
                        invoice.status = "paid"
                    if hasattr(invoice, "paid_date"):
                        invoice.paid_date = datetime.utcnow()

                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

    return render_template_string(_SUCCESS_TEMPLATE, session_id=session_id, invoice_id=invoice_id), 200


@payment_redirects_bp.route("/payment/cancel")
def payment_cancel():
    session_id = request.args.get("session_id")
    invoice_id = None

    if session_id:
        payment_intent = PaymentIntent.query.filter_by(client_secret=session_id).first()
        if payment_intent:
            invoice_id = str(payment_intent.invoice_id) if payment_intent.invoice_id else None

            if payment_intent.status not in {"canceled", "succeeded"}:
                payment_intent.status = "canceled"

                invoice = payment_intent.invoice or Invoice.query.get(payment_intent.invoice_id)
                if invoice and hasattr(invoice, "payment_status"):
                    invoice.payment_status = "canceled"

                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

    return render_template_string(_CANCEL_TEMPLATE, session_id=session_id, invoice_id=invoice_id), 200
