"""
Unit and integration tests for ResendEmailService and email management commands.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core import mail
from django.core.management import call_command, CommandError
from resend.exceptions import ResendError

from common.services.email import ResendEmailService, email_service
from users.models import User


class EmailServiceUnitTests(TestCase):
    def setUp(self):
        self.default_api_key = "re_test_key_123456789"
        self.service = ResendEmailService(
            api_key=self.default_api_key,
            default_from="Homepoint <notifications@test.com>",
            support_email="support@test.com",
        )

    def test_initialization_defaults(self):
        """Service should initialize with sensible defaults or provided arguments."""
        self.assertEqual(self.service.api_key, self.default_api_key)
        self.assertEqual(self.service.default_from, "Homepoint <notifications@test.com>")
        self.assertEqual(self.service.support_email, "support@test.com")

    def test_normalize_recipients(self):
        """Single email string and list of strings should be normalized correctly."""
        self.assertEqual(
            self.service._normalize_recipients("user@example.com"),
            ["user@example.com"],
        )
        self.assertEqual(
            self.service._normalize_recipients([" a@b.com ", "c@d.com"]),
            ["a@b.com", "c@d.com"],
        )
        with self.assertRaises(ValueError):
            self.service._normalize_recipients("")
        with self.assertRaises(ValueError):
            self.service._normalize_recipients([])

    def test_get_user_email_and_name_from_string(self):
        """String email input should extract email and derived name."""
        email, name = self.service._get_user_email_and_name("john.doe@example.com")
        self.assertEqual(email, "john.doe@example.com")
        self.assertEqual(name, "John.doe")

    def test_get_user_email_and_name_from_user_instance(self):
        """User model instance should return user email and full name or username."""
        mock_user = MagicMock()
        mock_user.email = "alex@example.com"
        mock_user.get_full_name.return_value = "Alex Mercer"
        mock_user.username = "alexm"

        email, name = self.service._get_user_email_and_name(mock_user)
        self.assertEqual(email, "alex@example.com")
        self.assertEqual(name, "Alex Mercer")

        # Fallback when get_full_name is empty
        mock_user.get_full_name.return_value = ""
        mock_user.first_name = ""
        email, name = self.service._get_user_email_and_name(mock_user)
        self.assertEqual(name, "alexm")

    def test_get_user_email_and_name_without_email_raises_error(self):
        """User object without email should raise ValueError."""
        mock_user = MagicMock(spec=[])
        with self.assertRaises(ValueError):
            self.service._get_user_email_and_name(mock_user)

    @patch("resend.Emails.send")
    def test_send_email_success_with_resend(self, mock_send):
        """Successful send via Resend SDK should return (True, response_dict)."""
        mock_send.return_value = {"id": "re_email_abc123"}

        success, response = self.service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test Body</p>",
            text_content="Test Body",
            tags=[{"name": "category", "value": "test"}],
        )

        self.assertTrue(success)
        self.assertEqual(response, {"id": "re_email_abc123"})
        mock_send.assert_called_once()
        call_params = mock_send.call_args[0][0]
        self.assertEqual(call_params["to"], ["recipient@example.com"])
        self.assertEqual(call_params["from"], "Homepoint <notifications@test.com>")
        self.assertEqual(call_params["subject"], "Test Subject")
        self.assertEqual(call_params["html"], "<p>Test Body</p>")
        self.assertEqual(call_params["text"], "Test Body")
        self.assertEqual(call_params["tags"], [{"name": "category", "value": "test"}])
        self.assertEqual(call_params["reply_to"], "support@test.com")

    @patch("resend.Emails.send")
    def test_send_email_resend_error_handled_gracefully(self, mock_send):
        """ResendError should be logged and return (False, error_str)."""
        mock_send.side_effect = ResendError(
            code=403,
            error_type="validation_error",
            message="Domain not verified",
            suggested_action="Verify domain in dashboard",
        )

        success, response = self.service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test Body</p>",
        )

        self.assertFalse(success)
        self.assertIn("Domain not verified", str(response))

    @patch("resend.Emails.send")
    def test_send_email_general_exception_handled_gracefully(self, mock_send):
        """Unexpected exception should be caught and return (False, error_str)."""
        mock_send.side_effect = ConnectionError("Network unreachable")

        success, response = self.service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test Body</p>",
        )

        self.assertFalse(success)
        self.assertIn("Network unreachable", str(response))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        RESEND_API_KEY=None,
    )
    def test_send_email_django_fallback_when_no_api_key(self):
        """When api_key is None, email should fallback to Django EMAIL_BACKEND."""
        service_no_key = ResendEmailService(api_key=None)
        mail.outbox = []

        success, response = service_no_key.send_email(
            to_email="dev@example.com",
            subject="Dev Subject",
            html_content="<h1>Dev HTML</h1>",
            text_content="Dev Plain",
        )

        self.assertTrue(success)
        self.assertEqual(response["id"], "django-fallback")
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.subject, "Dev Subject")
        self.assertEqual(sent.to, ["dev@example.com"])
        self.assertEqual(sent.body, "Dev Plain")
        self.assertEqual(sent.alternatives[0][0], "<h1>Dev HTML</h1>")

    @patch("resend.Emails.send")
    def test_send_template_email_renders_html_and_companion_txt(self, mock_send):
        """send_template_email should render the HTML and txt template files."""
        mock_send.return_value = {"id": "re_template_123"}

        success, response = self.service.send_template_email(
            to_email="user@example.com",
            subject="Welcome!",
            template_name="emails/welcome.html",
            context={"name": "Alice", "email": "user@example.com"},
        )

        self.assertTrue(success)
        mock_send.assert_called_once()
        params = mock_send.call_args[0][0]
        self.assertIn("Welcome aboard, Alice!", params["html"])
        self.assertIn("Alice", params["text"])

    @patch("resend.Emails.send")
    def test_predefined_welcome_email(self, mock_send):
        """send_welcome_email should construct correct context and tags."""
        mock_send.return_value = {"id": "re_welcome_123"}

        mock_user = MagicMock()
        mock_user.email = "newuser@example.com"
        mock_user.get_full_name.return_value = "Jane Doe"
        mock_user.role = "cashier"

        success, response = self.service.send_welcome_email(mock_user)
        self.assertTrue(success)
        params = mock_send.call_args[0][0]
        self.assertIn("Welcome to Homepoint POS, Jane Doe!", params["subject"])
        self.assertEqual(params["tags"], [{"name": "category", "value": "welcome"}])

    @patch("resend.Emails.send")
    def test_predefined_password_reset_email(self, mock_send):
        """send_password_reset_email should include reset link and expiration notice."""
        mock_send.return_value = {"id": "re_reset_123"}

        mock_user = MagicMock()
        mock_user.email = "forgot@example.com"
        mock_user.get_full_name.return_value = "Bob Smith"

        reset_url = "https://example.com/reset?token=xyz"
        success, response = self.service.send_password_reset_email(mock_user, reset_url)

        self.assertTrue(success)
        params = mock_send.call_args[0][0]
        self.assertEqual(params["subject"], "Reset Your Homepoint Password")
        self.assertIn(reset_url, params["html"])
        self.assertEqual(params["tags"], [{"name": "category", "value": "password_reset"}])

    @patch("resend.Emails.send")
    def test_predefined_password_reset_otp_email(self, mock_send):
        """send_password_reset_otp_email should include OTP code, valid minutes, and category tag."""
        mock_send.return_value = {"id": "re_otp_123"}

        mock_user = MagicMock()
        mock_user.email = "reset_user@example.com"
        mock_user.get_full_name.return_value = "Sam Green"

        success, response = self.service.send_password_reset_otp_email(
            user=mock_user,
            otp="654321",
            valid_minutes=6,
        )

        self.assertTrue(success)
        params = mock_send.call_args[0][0]
        self.assertEqual(params["subject"], "Your Homepoint Verification Code: 654321")
        self.assertIn("654321", params["html"])
        self.assertIn("6 minutes", params["html"])
        self.assertIn("654321", params["text"])
        self.assertEqual(params["tags"], [{"name": "category", "value": "password_reset_otp"}])

    @patch("resend.Emails.send")
    def test_predefined_notification_email(self, mock_send):
        """send_notification_email should format title and message."""
        mock_send.return_value = {"id": "re_notif_123"}

        mock_user = MagicMock()
        mock_user.email = "manager@example.com"
        mock_user.get_full_name.return_value = "Store Manager"

        success, response = self.service.send_notification_email(
            user=mock_user,
            title="Daily Sales Summary Ready",
            message="Sales reached KES 150,000 today.",
        )

        self.assertTrue(success)
        params = mock_send.call_args[0][0]
        self.assertEqual(params["subject"], "Daily Sales Summary Ready")
        self.assertIn("Sales reached KES 150,000 today.", params["html"])
        self.assertEqual(params["tags"], [{"name": "category", "value": "notification"}])


class SendTestEmailCommandTests(TestCase):
    def test_command_requires_valid_email(self):
        """Command should reject invalid email formats."""
        with self.assertRaises(CommandError):
            call_command("send_test_email", to="invalid-email-format")

    def test_command_dry_run_does_not_send_email(self):
        """--dry-run should render templates and exit cleanly without calling email service."""
        with patch.object(ResendEmailService, "send_email") as mock_send:
            call_command("send_test_email", to="admin@example.com", template="welcome", dry_run=True)
            mock_send.assert_not_called()

    @patch.object(ResendEmailService, "send_email")
    def test_command_live_raw_execution(self, mock_send):
        """Command should invoke email service with raw template by default."""
        mock_send.return_value = (True, {"id": "cmd_test_id"})
        call_command("send_test_email", to="admin@example.com")
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args[1]["to_email"], "admin@example.com")
