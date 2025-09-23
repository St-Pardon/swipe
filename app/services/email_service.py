from flask import current_app, render_template_string
from flask_mail import Message
from app.extensions import mail
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_email(to, subject, template=None, **kwargs):
        """Send email with template"""
        try:
            if not current_app.config.get('MAIL_SERVER'):
                logger.warning("Mail server not configured. Email not sent.")
                return False
                
            if current_app.config.get('MAIL_SUPPRESS_SEND'):
                logger.info(f"Email suppressed: {subject} to {to}")
                return True
            
            msg = Message(
                subject=subject,
                recipients=[to] if isinstance(to, str) else to,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            if template:
                msg.html = render_template_string(template, **kwargs)
            else:
                msg.body = kwargs.get('body', '')
            
            mail.send(msg)
            logger.info(f"Email sent successfully: {subject} to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_email(user_email, user_name, verification_token):
        """Send email verification email"""
        subject = "Verify Your Email - Swipe Payment"
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #007bff; text-align: center;">Email Verification Required</h2>
                <p>Hello {{ user_name }},</p>
                <p>Welcome to Swipe Payment! Please verify your email address to activate your account.</p>
                <p>Click the button below to verify your email:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ verification_url }}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Verify Email Address</a>
                </div>
                <p>Or copy and paste this link in your browser:</p>
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; word-break: break-all; margin: 20px 0;">
                    {{ verification_url }}
                </div>
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <strong>Important:</strong> This verification link will expire in 24 hours for security reasons.
                </div>
                <p>If you did not create an account with Swipe Payment, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from Swipe Payment. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """

        from flask import url_for
        verification_url = url_for('auth.verify_email', token=verification_token, _external=True)

        return EmailService.send_email(
            to=user_email,
            subject=subject,
            template=template,
            user_name=user_name,
            verification_url=verification_url
        )

    @staticmethod
    def send_password_reset_email(user_email, reset_token):
        subject = "Password Reset - Swipe Payment"
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; text-align: center;">Password Reset Request</h2>
                <p>Hello,</p>
                <p>You have requested to reset your password for your Swipe Payment account.</p>
                <p>Your password reset token is:</p>
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 16px; text-align: center; margin: 20px 0;">
                    {{ reset_token }}
                </div>
                <p><strong>This token will expire in 1 hour.</strong></p>
                <p>If you did not request this password reset, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from Swipe Payment. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=user_email,
            subject=subject,
            template=template,
            reset_token=reset_token
        )
    
    @staticmethod
    def send_2fa_setup_email(user_email, user_name):
        """Send 2FA setup confirmation email"""
        subject = "Two-Factor Authentication Enabled - Swipe Payment"
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #28a745; text-align: center;">🔐 Two-Factor Authentication Enabled</h2>
                <p>Hello {{ user_name }},</p>
                <p>Two-factor authentication has been successfully enabled for your Swipe Payment account.</p>
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <strong>Your account is now more secure!</strong>
                    <ul style="margin: 10px 0;">
                        <li>You'll need your authenticator app to log in</li>
                        <li>Keep your backup codes in a safe place</li>
                        <li>You can disable 2FA anytime in your account settings</li>
                    </ul>
                </div>
                <p>If you did not enable 2FA, please contact support immediately.</p>
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from Swipe Payment. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=user_email,
            subject=subject,
            template=template,
            user_name=user_name
        )
    
    @staticmethod
    def send_login_notification_email(user_email, user_name, ip_address, location="Unknown"):
        """Send login notification email"""
        subject = "New Login to Your Account - Swipe Payment"
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; text-align: center;">New Login Detected</h2>
                <p>Hello {{ user_name }},</p>
                <p>We detected a new login to your Swipe Payment account:</p>
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <strong>Login Details:</strong><br>
                    <strong>IP Address:</strong> {{ ip_address }}<br>
                    <strong>Location:</strong> {{ location }}<br>
                    <strong>Time:</strong> {{ login_time }}
                </div>
                <p>If this was you, no action is needed.</p>
                <p><strong>If this wasn't you:</strong></p>
                <ul>
                    <li>Change your password immediately</li>
                    <li>Enable two-factor authentication</li>
                    <li>Contact our support team</li>
                </ul>
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from Swipe Payment. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        from datetime import datetime
        return EmailService.send_email(
            to=user_email,
            subject=subject,
            template=template,
            user_name=user_name,
            ip_address=ip_address,
            location=location,
            login_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )
    
    @staticmethod
    def send_transaction_notification_email(user_email, user_name, transaction_type, amount, currency):
        """Send transaction notification email"""
        subject = f"Transaction Notification - {transaction_type.title()} - Swipe Payment"
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; text-align: center;">Transaction Notification</h2>
                <p>Hello {{ user_name }},</p>
                <p>A {{ transaction_type }} transaction has been processed on your account:</p>
                <div style="background-color: #e9ecef; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <strong>Transaction Details:</strong><br>
                    <strong>Type:</strong> {{ transaction_type.title() }}<br>
                    <strong>Amount:</strong> {{ amount }} {{ currency }}<br>
                    <strong>Time:</strong> {{ transaction_time }}
                </div>
                <p>You can view all your transactions in your account dashboard.</p>
                <p>If you have any questions about this transaction, please contact our support team.</p>
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px;">
                    This is an automated message from Swipe Payment. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        from datetime import datetime
        return EmailService.send_email(
            to=user_email,
            subject=subject,
            template=template,
            user_name=user_name,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            transaction_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )
