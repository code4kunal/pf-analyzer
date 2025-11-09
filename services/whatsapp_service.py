"""
WhatsApp Integration Service
Send questionnaire invites and notifications via WhatsApp

Supports multiple WhatsApp APIs:
1. Twilio WhatsApp Business API (Recommended for production)
2. WhatsApp Business API (Official, requires approval)
3. WATI.io / Interakt / AiSensy (Indian providers)
"""

import requests
from typing import Optional, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Service for sending WhatsApp messages

    Setup Instructions:
    1. Twilio (Easiest to start):
       - Sign up at twilio.com
       - Get WhatsApp-enabled phone number
       - Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER to config

    2. WATI.io (Good for India):
       - Sign up at wati.io
       - Get API key
       - Add WATI_API_KEY, WATI_API_URL to config

    3. WhatsApp Business API (Enterprise):
       - Apply for official access
       - Requires business verification
    """

    # Twilio Configuration
    TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    # WATI Configuration (Indian provider)
    WATI_API_URL = "https://live-server-XXXX.wati.io/api/v1/sendTemplateMessage"

    @staticmethod
    def send_via_twilio(
        to_phone: str,
        message: str,
        account_sid: str,
        auth_token: str,
        from_whatsapp_number: str
    ) -> Dict:
        """
        Send WhatsApp message via Twilio

        Args:
            to_phone: Recipient phone number in format +91XXXXXXXXXX
            message: Message text
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_whatsapp_number: Twilio WhatsApp number (e.g., whatsapp:+14155238886)

        Returns:
            Dictionary with send result
        """
        try:
            # Format phone numbers
            if not to_phone.startswith('whatsapp:'):
                to_phone = f"whatsapp:{to_phone}"
            if not from_whatsapp_number.startswith('whatsapp:'):
                from_whatsapp_number = f"whatsapp:{from_whatsapp_number}"

            url = WhatsAppService.TWILIO_API_URL.format(account_sid=account_sid)

            data = {
                'From': from_whatsapp_number,
                'To': to_phone,
                'Body': message
            }

            response = requests.post(
                url,
                data=data,
                auth=(account_sid, auth_token),
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"WhatsApp sent via Twilio to {to_phone}: SID {result.get('sid')}")

            return {
                'success': True,
                'provider': 'twilio',
                'message_sid': result.get('sid'),
                'status': result.get('status'),
                'error': None
            }

        except Exception as e:
            logger.error(f"Error sending WhatsApp via Twilio: {str(e)}")
            return {
                'success': False,
                'provider': 'twilio',
                'message_sid': None,
                'status': 'failed',
                'error': str(e)
            }

    @staticmethod
    def send_via_wati(
        to_phone: str,
        template_name: str,
        parameters: Dict,
        api_key: str,
        api_url: str
    ) -> Dict:
        """
        Send WhatsApp message via WATI.io (Indian provider)

        Args:
            to_phone: Recipient phone number (91XXXXXXXXXX format)
            template_name: Name of approved WhatsApp template
            parameters: Template parameters
            api_key: WATI API key
            api_url: WATI API endpoint URL

        Returns:
            Dictionary with send result
        """
        try:
            # Remove + if present
            phone = to_phone.replace('+', '').replace(' ', '')

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'whatsappNumber': phone,
                'template_name': template_name,
                'broadcast_name': 'Client Profiling Questionnaire',
                'parameters': parameters
            }

            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"WhatsApp sent via WATI to {to_phone}")

            return {
                'success': True,
                'provider': 'wati',
                'message_id': result.get('id'),
                'status': 'sent',
                'error': None
            }

        except Exception as e:
            logger.error(f"Error sending WhatsApp via WATI: {str(e)}")
            return {
                'success': False,
                'provider': 'wati',
                'message_id': None,
                'status': 'failed',
                'error': str(e)
            }

    @staticmethod
    def send_questionnaire_invite(
        recipient_name: str,
        recipient_phone: str,
        invite_url: str,
        custom_message: Optional[str] = None,
        provider: str = "twilio",
        **credentials
    ) -> Dict:
        """
        Send questionnaire invite via WhatsApp

        Args:
            recipient_name: Recipient's name
            recipient_phone: Phone number (+91XXXXXXXXXX)
            invite_url: Full questionnaire URL
            custom_message: Optional personalized message
            provider: 'twilio' or 'wati'
            **credentials: Provider credentials (account_sid, auth_token, api_key, etc.)

        Returns:
            Send result dictionary
        """
        # Build message
        greeting = f"Hello {recipient_name}! 👋\n\n"

        if custom_message:
            intro = custom_message + "\n\n"
        else:
            intro = "Thank you for your interest in our financial planning services!\n\n"

        body = (
            "We'd love to understand your financial goals and risk profile to prepare "
            "a personalized investment plan for you.\n\n"
            "📋 Please complete this short questionnaire (takes 5-7 minutes):\n"
            f"{invite_url}\n\n"
            "The questionnaire covers:\n"
            "✅ Your financial goals (retirement, education, etc.)\n"
            "✅ Risk assessment with detailed explanations\n"
            "✅ Investment preferences and timeline\n"
            "✅ Current financial situation\n\n"
            "Why fill this?\n"
            "💡 We'll prepare 2-3 adaptive investment plans based on your profile\n"
            "💡 Better understanding = More personalized recommendations\n"
            "💡 Saves time in our first meeting\n\n"
            "All information is confidential and secure. 🔒\n\n"
            "Looking forward to helping you achieve your financial goals!\n\n"
            "Best regards,\n"
            "Your Financial Planning Team"
        )

        full_message = greeting + intro + body

        # Send based on provider
        if provider == "twilio":
            return WhatsAppService.send_via_twilio(
                to_phone=recipient_phone,
                message=full_message,
                account_sid=credentials.get('account_sid'),
                auth_token=credentials.get('auth_token'),
                from_whatsapp_number=credentials.get('from_whatsapp_number')
            )
        elif provider == "wati":
            # For WATI, you'd use a pre-approved template
            # This is a simplified example - actual implementation depends on your approved templates
            parameters = {
                'name': recipient_name,
                'questionnaire_link': invite_url
            }
            return WhatsAppService.send_via_wati(
                to_phone=recipient_phone,
                template_name='questionnaire_invite',  # Must be pre-approved by WhatsApp
                parameters=parameters,
                api_key=credentials.get('api_key'),
                api_url=credentials.get('api_url')
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def send_completion_notification(
        recipient_name: str,
        recipient_phone: str,
        team_member_name: str,
        meeting_suggestion: Optional[str] = None,
        provider: str = "twilio",
        **credentials
    ) -> Dict:
        """
        Send thank you message after questionnaire completion

        Args:
            recipient_name: Client's name
            recipient_phone: Phone number
            team_member_name: Name of team member who will contact
            meeting_suggestion: Optional meeting time suggestion
            provider: WhatsApp provider
            **credentials: Provider credentials

        Returns:
            Send result
        """
        message = (
            f"Thank you {recipient_name}! 🙏\n\n"
            "We've received your questionnaire responses and are analyzing your financial profile.\n\n"
            f"Our expert {team_member_name} will reach out to you within 24 hours with:\n"
            "📊 Personalized investment recommendations\n"
            "📈 Multiple portfolio options based on your risk profile\n"
            "💰 Detailed projections for your financial goals\n\n"
        )

        if meeting_suggestion:
            message += f"Suggested meeting time: {meeting_suggestion}\n\n"

        message += (
            "In the meantime, you can:\n"
            "• Review our investment philosophy on our website\n"
            "• Prepare any questions you'd like to discuss\n"
            "• Gather details of your existing investments\n\n"
            "We're excited to help you achieve your financial dreams! 🎯\n\n"
            "Best regards,\n"
            "Your Financial Planning Team"
        )

        if provider == "twilio":
            return WhatsAppService.send_via_twilio(
                to_phone=recipient_phone,
                message=message,
                account_sid=credentials.get('account_sid'),
                auth_token=credentials.get('auth_token'),
                from_whatsapp_number=credentials.get('from_whatsapp_number')
            )
        elif provider == "wati":
            parameters = {
                'name': recipient_name,
                'team_member': team_member_name
            }
            return WhatsAppService.send_via_wati(
                to_phone=recipient_phone,
                template_name='questionnaire_completed',
                parameters=parameters,
                api_key=credentials.get('api_key'),
                api_url=credentials.get('api_url')
            )

    @staticmethod
    def format_indian_phone(phone: str) -> str:
        """
        Format phone number for Indian numbers

        Args:
            phone: Phone number in various formats

        Returns:
            Formatted phone number (+91XXXXXXXXXX)
        """
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Remove + if present
        cleaned = cleaned.replace('+', '')

        # Add country code if not present
        if not cleaned.startswith('91'):
            if len(cleaned) == 10:
                cleaned = '91' + cleaned

        # Add + prefix
        return '+' + cleaned

    @staticmethod
    def validate_phone(phone: str) -> tuple[bool, Optional[str]]:
        """
        Validate phone number format

        Args:
            phone: Phone number string

        Returns:
            Tuple of (is_valid, error_message)
        """
        formatted = WhatsAppService.format_indian_phone(phone)

        # Check format
        if not formatted.startswith('+91'):
            return False, "Phone must be an Indian number (+91)"

        # Check length (should be +91 followed by 10 digits)
        if len(formatted) != 13:
            return False, f"Invalid phone length: {len(formatted)}. Expected +91 followed by 10 digits"

        # Check all digits after +91
        if not formatted[3:].isdigit():
            return False, "Phone number contains non-digit characters"

        return True, None
