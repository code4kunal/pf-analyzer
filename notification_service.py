import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        # Email configuration (using environment variables for security)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        # Twilio configuration (optional)
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

        # SendGrid configuration (optional)
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

        # Initialize Twilio client if credentials are available
        self.twilio_client = None
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
            except ImportError:
                logger.warning("Twilio not installed. SMS notifications disabled.")

        # Initialize SendGrid if API key is available
        self.sendgrid_client = None
        if self.sendgrid_api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(api_key=self.sendgrid_api_key)
            except ImportError:
                logger.warning("SendGrid not installed. Using SMTP for email notifications.")

    async def send_email_smtp(self, to_email: str, subject: str, message: str, html_message: Optional[str] = None) -> bool:
        """Send email using SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured. Email not sent.")
                return False

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email

            # Add text part
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)

            # Add HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, 'html')
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False

    async def send_email_sendgrid(self, to_email: str, subject: str, message: str, html_message: Optional[str] = None) -> bool:
        """Send email using SendGrid"""
        try:
            if not self.sendgrid_client:
                return await self.send_email_smtp(to_email, subject, message, html_message)

            from sendgrid.helpers.mail import Mail

            # Create email
            mail = Mail(
                from_email=self.smtp_username or "noreply@portfolio-analyzer.com",
                to_emails=to_email,
                subject=subject,
                plain_text_content=message,
                html_content=html_message or message
            )

            # Send email
            response = self.sendgrid_client.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent successfully via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"❌ SendGrid failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to send email via SendGrid to {to_email}: {e}")
            # Fallback to SMTP
            return await self.send_email_smtp(to_email, subject, message, html_message)

    async def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS using Twilio"""
        try:
            if not self.twilio_client or not self.twilio_phone_number:
                logger.warning("Twilio not configured. SMS not sent.")
                return False

            # Send SMS
            sms = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_phone
            )

            logger.info(f"✅ SMS sent successfully to {to_phone} (SID: {sms.sid})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send SMS to {to_phone}: {e}")
            return False

    async def send_price_alert(self, user_email: str, user_phone: str, symbol: str, alert_type: str, current_price: float, trigger_price: float) -> dict:
        """Send price alert via email and SMS"""
        # Create message content
        if alert_type == "TARGET_REACHED":
            subject = f"🎯 Target Reached: {symbol}"
            message = f"Great news! {symbol} has reached your target price of ₹{trigger_price}.\n\nCurrent Price: ₹{current_price}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nConsider taking action on your position."
        else:
            subject = f"🚨 Stop Loss Triggered: {symbol}"
            message = f"Alert! {symbol} has hit your stop loss of ₹{trigger_price}.\n\nCurrent Price: ₹{current_price}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nPlease review your position immediately."

        # HTML version for email
        html_message = f"""
        <html>
        <body>
            <h2>{'🎯 Target Reached' if alert_type == 'TARGET_REACHED' else '🚨 Stop Loss Alert'}</h2>
            <p><strong>Symbol:</strong> {symbol}</p>
            <p><strong>{'Target' if alert_type == 'TARGET_REACHED' else 'Stop Loss'} Price:</strong> ₹{trigger_price}</p>
            <p><strong>Current Price:</strong> ₹{current_price}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <p>{'Consider taking action on your position.' if alert_type == 'TARGET_REACHED' else 'Please review your position immediately.'}</p>
            <p><em>Portfolio Analyzer - Your Trading Assistant</em></p>
        </body>
        </html>
        """

        # Send notifications
        results = {
            'email_sent': False,
            'sms_sent': False
        }

        # Send email
        if user_email:
            results['email_sent'] = await self.send_email_sendgrid(user_email, subject, message, html_message)

        # Send SMS (shorter message for SMS)
        if user_phone:
            sms_message = f"{symbol}: {'Target ₹{trigger_price} reached!' if alert_type == 'TARGET_REACHED' else 'Stop loss ₹{trigger_price} hit!'} Current: ₹{current_price}"
            results['sms_sent'] = await self.send_sms(user_phone, sms_message)

        return results

# Global instance
notification_service = NotificationService()