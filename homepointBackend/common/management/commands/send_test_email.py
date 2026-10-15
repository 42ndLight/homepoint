import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings

from common.services.email import ResendEmailService


class Command(BaseCommand):
    help = "Send a test email using Resend or verify template rendering."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            type=str,
            required=True,
            help="Recipient email address (e.g. user@example.com)",
        )
        parser.add_argument(
            "--template",
            type=str,
            default="raw",
            choices=["raw", "welcome", "password_reset", "notification"],
            help="Template type to send (raw, welcome, password_reset, notification)",
        )
        parser.add_argument(
            "--subject",
            type=str,
            default=None,
            help="Custom subject line",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Render templates and validate parameters without calling external email services.",
        )

    def handle(self, *args, **options):
        to_email = options["to"].strip()
        template_choice = options["template"]
        subject = options.get("subject")
        dry_run = options.get("dry_run", False)

        try:
            validate_email(to_email)
        except ValidationError:
            raise CommandError(f"Invalid email address provided: '{to_email}'")

        service = ResendEmailService()
        self.stdout.write(self.style.NOTICE(f"=== Homepoint Email Service Diagnostic ==="))
        self.stdout.write(f"Recipient: {to_email}")
        self.stdout.write(f"Default From: {service.default_from}")
        self.stdout.write(f"Support Email: {service.support_email}")
        self.stdout.write(
            f"Resend API Key Configured: {'Yes (length: %d)' % len(service.api_key) if service.api_key else 'No (using Django fallback)'}"
        )
        self.stdout.write(f"Selected Template: {template_choice}")
        self.stdout.write(f"Dry Run Mode: {dry_run}\n")

        if dry_run:
            self.stdout.write(self.style.WARNING("Performing dry run - rendering template only..."))
            if template_choice == "welcome":
                subj = subject or "Welcome to Homepoint POS!"
                context = {
                    "app_name": "Homepoint POS",
                    "support_email": service.support_email,
                    "name": to_email.split("@")[0].capitalize(),
                    "email": to_email,
                    "role": "Staff",
                    "frontend_url": getattr(settings, "FRONTEND_URL", "http://localhost:5173"),
                    "current_year": 2026,
                }
                template_name = "emails/welcome.html"
            elif template_choice == "password_reset":
                subj = subject or "Reset Your Homepoint Password"
                context = {
                    "app_name": "Homepoint POS",
                    "support_email": service.support_email,
                    "name": to_email.split("@")[0].capitalize(),
                    "email": to_email,
                    "reset_link": "https://example.com/reset-password?token=sample-test-token",
                    "valid_minutes": 15,
                    "current_year": 2026,
                }
                template_name = "emails/password_reset.html"
            elif template_choice == "notification":
                subj = subject or "Homepoint System Notification"
                context = {
                    "app_name": "Homepoint POS",
                    "support_email": service.support_email,
                    "name": to_email.split("@")[0].capitalize(),
                    "title": "System Diagnostic Test",
                    "message": "This is a dry-run test notification from the Homepoint POS backend.",
                    "current_year": 2026,
                }
                template_name = "emails/notification.html"
            else:
                subj = subject or "Homepoint Raw Diagnostic Email"
                context = {}
                template_name = None

            self.stdout.write(self.style.SUCCESS(f"Subject: {subj}"))
            if template_name:
                from django.template.loader import render_to_string
                rendered = render_to_string(template_name, context)
                self.stdout.write(f"Rendered Template ({template_name}):\n{'-'*40}\n{rendered[:300]}...\n{'-'*40}")
            self.stdout.write(self.style.SUCCESS("Dry run completed successfully. No emails sent."))
            return

        # Live or Django-fallback execution
        self.stdout.write("Dispatching email...")
        if template_choice == "welcome":
            success, result = service.send_welcome_email(to_email)
        elif template_choice == "password_reset":
            reset_url = "https://example.com/reset-password?token=sample-test-token"
            success, result = service.send_password_reset_email(to_email, reset_url)
        elif template_choice == "notification":
            title = subject or "Homepoint Test Notification"
            message = "This is a live test notification generated from the Homepoint POS management command."
            success, result = service.send_notification_email(to_email, title, message)
        else:
            subj = subject or "Homepoint Test Email"
            html = f"""
            <h2>Homepoint Test Email</h2>
            <p>This is a live test message from <strong>Homepoint POS</strong>.</p>
            <p>If you received this message, your email delivery pipeline is configured correctly.</p>
            """
            success, result = service.send_email(
                to_email=to_email,
                subject=subj,
                html_content=html,
                tags=[{"name": "category", "value": "diagnostic"}],
            )

        if success:
            self.stdout.write(self.style.SUCCESS(f"SUCCESS: Email dispatched successfully!"))
            self.stdout.write(f"Response: {result}")
        else:
            self.stdout.write(self.style.ERROR(f"FAILURE: Failed to dispatch email."))
            self.stdout.write(f"Error details: {result}")
            sys.exit(1)
