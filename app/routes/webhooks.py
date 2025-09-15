from flask import Blueprint, request, jsonify, current_app
import stripe
import logging
from app.config.payment_config import PaymentConfig
from app.services.payment_service import PaymentService
from app.models.payment_intent_model import PaymentIntent
from app.models.payout_model import Payout
from app.extensions import db

webhooks_bp = Blueprint('webhooks', __name__)
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = PaymentConfig.STRIPE_SECRET_KEY

@webhooks_bp.route('/webhooks/stripe', methods=['POST'])
def handle_stripe_webhook():
    """
    Handle Stripe webhook events
    """
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, PaymentConfig.STRIPE_WEBHOOK_SECRET
        )
        
        logger.info(f"Received Stripe webhook: {event['type']}")
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event['data']['object'])
        
        elif event['type'] == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event['data']['object'])
        
        elif event['type'] == 'checkout.session.completed':
            handle_checkout_session_completed(event['data']['object'])
        
        elif event['type'] == 'payout.paid':
            handle_payout_paid(event['data']['object'])
        
        elif event['type'] == 'payout.failed':
            handle_payout_failed(event['data']['object'])
        
        elif event['type'] == 'payment_intent.canceled':
            handle_payment_intent_canceled(event['data']['object'])
        
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return jsonify({'status': 'success'}), 200
        
    except ValueError as e:
        logger.error(f"Invalid payload in webhook: {str(e)}")
        return jsonify({'error': 'Invalid payload'}), 400
    
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature in webhook: {str(e)}")
        return jsonify({'error': 'Invalid signature'}), 400
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500

def handle_payment_intent_succeeded(payment_intent_data):
    """
    Handle successful payment intent
    """
    try:
        payment_intent_id = payment_intent_data['id']
        logger.info(f"Processing successful payment intent: {payment_intent_id}")
        
        # Use PaymentService to handle the successful payment
        PaymentService.handle_successful_payment(payment_intent_id)
        
        logger.info(f"Successfully processed payment intent: {payment_intent_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment_intent.succeeded: {str(e)}")
        raise

def handle_payment_intent_failed(payment_intent_data):
    """
    Handle failed payment intent
    """
    try:
        payment_intent_id = payment_intent_data['id']
        logger.info(f"Processing failed payment intent: {payment_intent_id}")
        
        # Get local payment intent
        payment_intent = PaymentService.get_payment_intent_by_id(payment_intent_id)
        
        if payment_intent:
            payment_intent.update_status('payment_failed')
            db.session.commit()
            
            logger.info(f"Updated payment intent {payment_intent_id} status to failed")
        else:
            logger.warning(f"Payment intent {payment_intent_id} not found in database")
            
    except Exception as e:
        logger.error(f"Error handling payment_intent.payment_failed: {str(e)}")
        db.session.rollback()
        raise

def handle_payment_intent_canceled(payment_intent_data):
    """
    Handle canceled payment intent
    """
    try:
        payment_intent_id = payment_intent_data['id']
        logger.info(f"Processing canceled payment intent: {payment_intent_id}")
        
        # Get local payment intent
        payment_intent = PaymentService.get_payment_intent_by_id(payment_intent_id)
        
        if payment_intent:
            payment_intent.update_status('canceled')
            db.session.commit()
            
            logger.info(f"Updated payment intent {payment_intent_id} status to canceled")
        else:
            logger.warning(f"Payment intent {payment_intent_id} not found in database")
            
    except Exception as e:
        logger.error(f"Error handling payment_intent.canceled: {str(e)}")
        db.session.rollback()
        raise

def handle_checkout_session_completed(session_data):
    """
    Handle completed checkout session (for invoice payments)
    """
    try:
        session_id = session_data['id']
        payment_intent_id = session_data.get('payment_intent')
        
        logger.info(f"Processing completed checkout session: {session_id}")
        
        if payment_intent_id:
            # Handle the successful payment
            PaymentService.handle_successful_payment(payment_intent_id)
            
            # Update the payment intent with checkout session info
            payment_intent = PaymentService.get_payment_intent_by_id(payment_intent_id)
            if payment_intent and payment_intent.metadata:
                payment_intent.metadata['checkout_session_completed'] = True
                db.session.commit()
        
        logger.info(f"Successfully processed checkout session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error handling checkout.session.completed: {str(e)}")
        raise

def handle_payout_paid(payout_data):
    """
    Handle successful payout
    """
    try:
        payout_id = payout_data['id']
        arrival_date = payout_data.get('arrival_date')
        
        logger.info(f"Processing successful payout: {payout_id}")
        
        # Get local payout
        payout = PaymentService.get_payout_by_id(payout_id)
        
        if payout:
            # Convert arrival_date timestamp to date if provided
            arrival_date_obj = None
            if arrival_date:
                from datetime import datetime
                arrival_date_obj = datetime.fromtimestamp(arrival_date).date()
            
            payout.update_status('paid', arrival_date=arrival_date_obj)
            db.session.commit()
            
            logger.info(f"Updated payout {payout_id} status to paid")
        else:
            logger.warning(f"Payout {payout_id} not found in database")
            
    except Exception as e:
        logger.error(f"Error handling payout.paid: {str(e)}")
        db.session.rollback()
        raise

def handle_payout_failed(payout_data):
    """
    Handle failed payout
    """
    try:
        payout_id = payout_data['id']
        failure_code = payout_data.get('failure_code')
        failure_message = payout_data.get('failure_message')
        
        logger.info(f"Processing failed payout: {payout_id}")
        
        # Get local payout
        payout = PaymentService.get_payout_by_id(payout_id)
        
        if payout:
            payout.update_status(
                'failed', 
                failure_code=failure_code,
                failure_message=failure_message
            )
            
            # Refund the amount back to the user's account
            if payout.account:
                payout.account.balance += payout.amount
                logger.info(f"Refunded {payout.amount} {payout.currency} back to account {payout.account_id}")
            
            db.session.commit()
            
            logger.info(f"Updated payout {payout_id} status to failed and refunded amount")
        else:
            logger.warning(f"Payout {payout_id} not found in database")
            
    except Exception as e:
        logger.error(f"Error handling payout.failed: {str(e)}")
        db.session.rollback()
        raise

@webhooks_bp.route('/webhooks/test', methods=['POST'])
def test_webhook():
    """
    Test endpoint for webhook functionality
    """
    try:
        data = request.get_json()
        logger.info(f"Test webhook received: {data}")
        
        return jsonify({
            'status': 'success',
            'message': 'Test webhook received successfully',
            'data': data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in test webhook: {str(e)}")
        return jsonify({'error': 'Test webhook failed'}), 500
