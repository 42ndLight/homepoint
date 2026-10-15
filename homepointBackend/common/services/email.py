"""
Modular Email Service for Homepoint using Resend and Django template rendering.

Features:
- Resend SDK integration for transactional emails.
- Standardized return format: (success: bool, response_or_error: dict | str).
- HTML template rendering with companion plaintext fallbacks and automatic strip_tags fallback.
- Graceful error handling and logging.
- Built-in fallback to Django's EMAIL_BACKEND (e.g. console/locmem) when RESEND_API_KEY is not configured.
- Pre-defined helpers for welcome, password reset, and transactional notifications.
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

import resend
from resend.exceptions import ResendError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class ResendEmailService:
    """
    Wrapper around Resend API with Django template rendering,
    pre-configured application workflows, and local development fallback.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_from: str | None = None,
        support_email: str | None = None,
    ) -> None:
        self.api_key = api_key or getattr(settings, 'RESEND_API_KEY', None)
        self.default_from = default_from or getattr(
            settings,
            'DEFAULT_FROM_EMAIL',
            'Homepoint <notifications@betasys.co.ke>'
        )
        self.support_email = support_email or getattr(
            settings,
            'SUPPORT_EMAIL',
            'support@betasys.co.ke'
        )

        if self.api_key:
            resend.api_key = self.api_key

    def _normalize_recipients(self, to_email: str | list[str]) -> list[str]:
        """Normalize recipient(s) to a clean list of email strings."""
        if isinstance(to_email, str):
            recipients = [to_email.strip()] if to_email.strip() else []
        else:
            recipients = [str(e).strip() for e in to_email if str(e).strip()]
        
        if not recipients:
            raise ValueError("Recipient email list cannot be empty.")
        return recipients

    def _get_user_email_and_name(self, user: Any) -> tuple[str, str]:
        """Extract email and display name from a User instance or email string."""
        if isinstance(user, str):
            email = user.strip()
            name = email.split('@')[0].capitalize()
            return email, name

        email = getattr(user, 'email', None)
        if not email:
            raise ValueError("Provided user object does not have an email address.")

        if hasattr(user, 'get_full_name'):
            name = user.get_full_name() or getattr(user, 'first_name', '') or getattr(user, 'username', 'Customer')
        else:
            name = getattr(user, 'username', 'Customer')

        return email, name

    def send_email(
        self,
        to_email: str | list[str],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        reply_to: str | list[str] | None = None,
        tags: list[dict[str, str]] | None = None,
        from_email: str | None = None,
    ) -> tuple[bool, dict | str]:
        """
        Send an email via Resend API or Django fallback.

        Args:
            to_email: Single recipient address or list of addresses.
            subject: Email subject line.
            html_content: HTML formatted email body.
            text_content: Optional plaintext alternative.
            reply_to: Optional reply-to address or list of addresses.
            tags: Optional list of dict tags e.g. [{'name': 'category', 'value': 'welcome'}].
            from_email: Sender address override.

        Returns:
            (True, response_dict) on success, or (False, error_str) on failure.
        """
        try:
            recipients = self._normalize_recipients(to_email)
            sender = from_email or self.default_from
            reply_to_addr = reply_to or self.support_email

            if not text_content:
                text_content = strip_tags(html_content)

            # Local development or test fallback when RESEND_API_KEY is not configured
            if not self.api_key:
                logger.info(
                    "RESEND_API_KEY is not configured. Sending email via Django EMAIL_BACKEND fallback: subject=%s recipient_count=%d",
                    subject,
                    len(recipients)
                )
                headers = {}
                if reply_to_addr:
                    headers['Reply-To'] = (
                        ','.join(reply_to_addr) if isinstance(reply_to_addr, list) else reply_to_addr
                    )

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=sender,
                    to=recipients,
                    headers=headers,
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                return True, {
                    "id": "django-fallback",
                    "status": "sent_via_django_backend",
                    "to": recipients,
                    "subject": subject,
                }

            # Resend API call
            resend.api_key = self.api_key
            params: dict[str, Any] = {
                "from": sender,
                "to": recipients,
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }

            if reply_to_addr:
                params["reply_to"] = reply_to_addr

            if tags:
                params["tags"] = tags

            response = resend.Emails.send(params)
            logger.info(
                 "Email sent successfully via Resend (recipient_count=%d, id: %s)",
                 len(recipients),
                 response.get('id'),
             )
            return True, response

        except ResendError as exc:
            logger.error(
                "Resend API error while sending email (recipient_count=%d)",
                len(recipients) if 'recipients' in locals() else 0,
                exc_info=True,
            )
            return False, str(exc)

        except Exception as exc:
            logger.error(
                "Failed to send email (recipient_count=%d)",
                len(recipients) if 'recipients' in locals() else 0,
                exc_info=True,
            )
            return False, str(exc)

    def send_template_email(
        self,
        to_email: str | list[str],
        subject: str,
        template_name: str,
        context: dict[str, Any] | None = None,
        tags: list[dict[str, str]] | None = None,
        reply_to: str | list[str] | None = None,
        from_email: str | None = None,
    ) -> tuple[bool, dict | str]:
        """
        Render Django HTML & plaintext email templates and send via Resend.

        Args:
            to_email: Recipient(s).
            subject: Subject line.
            template_name: Path to Django template (e.g., 'emails/welcome.html').
            context: Context dictionary passed to the template.
            tags: Resend tags.
            reply_to: Reply-to address.
            from_email: Sender address override.

        Returns:
            (True, response_dict) on success, or (False, error_str) on failure.
        """
        enriched_context = {
            "app_name": "Homepoint POS",
            "support_email": self.support_email,
            "current_year": datetime.now().year,
            "frontend_url": getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'),
            **(context or {}),
        }

        try:
            html_content = render_to_string(template_name, enriched_context)
        except Exception as exc:
            err = f"Template rendering failed for {template_name}: {exc}"
            logger.error(err, exc_info=True)
            return False, err

        # Check for companion .txt template (e.g. emails/welcome.txt)
        text_content = None
        if template_name.endswith('.html'):
            txt_template_name = template_name[:-5] + '.txt'
            try:
                text_content = render_to_string(txt_template_name, enriched_context)
            except TemplateDoesNotExist:
                text_content = strip_tags(html_content)
        else:
            text_content = strip_tags(html_content)

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            reply_to=reply_to,
            tags=tags,
            from_email=from_email,
        )

    # -------------------------------------------------------------------------
    # Pre-defined Use Case Helpers
    # -------------------------------------------------------------------------

    def send_welcome_email(self, user: Any) -> tuple[bool, dict | str]:
        """
        Send a welcome email to a newly registered user or staff member.
        """
        try:
            email, name = self._get_user_email_and_name(user)
        except ValueError as exc:
            logger.error("Cannot send welcome email: %s", exc)
            return False, str(exc)

        subject = f"Welcome to Homepoint POS, {name}!"
        context = {
            "user": user,
            "name": name,
            "email": email,
            "role": getattr(user, 'role', 'Customer').capitalize(),
        }
        tags = [{"name": "category", "value": "welcome"}]
        return self.send_template_email(
            to_email=email,
            subject=subject,
            template_name="emails/welcome.html",
            context=context,
            tags=tags,
        )

    def send_password_reset_email(self, user: Any, reset_link: str) -> tuple[bool, dict | str]:
        """
        Send a secure password reset link to a user.
        """
        try:
            email, name = self._get_user_email_and_name(user)
        except ValueError as exc:
            logger.error("Cannot send password reset email: %s", exc)
            return False, str(exc)

        subject = "Reset Your Homepoint Password"
        context = {
            "user": user,
            "name": name,
            "email": email,
            "reset_link": reset_link,
            "valid_minutes": 15,
        }
        tags = [{"name": "category", "value": "password_reset"}]
        return self.send_template_email(
            to_email=email,
            subject=subject,
            template_name="emails/password_reset.html",
            context=context,
            tags=tags,
        )

    def send_password_reset_otp_email(
        self,
        user: Any,
        otp: str,
        valid_minutes: int = 6,
    ) -> tuple[bool, dict | str]:
        """
        Send a one-time password (OTP) verification code to a user for password reset.
        """
        try:
            email, name = self._get_user_email_and_name(user)
        except ValueError as exc:
            logger.error("Cannot send password reset OTP email: %s", exc)
            return False, str(exc)

        subject = f"Your Homepoint Verification Code: {otp}"
        context = {
            "user": user,
            "name": name,
            "email": email,
            "otp": otp,
            "valid_minutes": valid_minutes,
        }
        tags = [{"name": "category", "value": "password_reset_otp"}]
        return self.send_template_email(
            to_email=email,
            subject=subject,
            template_name="emails/password_reset_otp.html",
            context=context,
            tags=tags,
        )

    def send_notification_email(self, user: Any, title: str, message: str) -> tuple[bool, dict | str]:
        """
        Send a generic transactional notification email to a user.
        """
        try:
            email, name = self._get_user_email_and_name(user)
        except ValueError as exc:
            logger.error("Cannot send notification email: %s", exc)
            return False, str(exc)

        subject = title
        context = {
            "user": user,
            "name": name,
            "email": email,
            "title": title,
            "message": message,
        }
        tags = [{"name": "category", "value": "notification"}]
        return self.send_template_email(
            to_email=email,
            subject=subject,
            template_name="emails/notification.html",
            context=context,
            tags=tags,
        )


# Default singleton instance
email_service = ResendEmailService()
