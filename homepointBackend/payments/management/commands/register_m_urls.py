# payments/management/commands/register_mpesa_urls.py

from django.core.management.base import BaseCommand
from django.conf import settings
from payments.mpesa.utils import get_mpesa_access_token  # your token function
import requests

class Command(BaseCommand):
    help = 'Register M-Pesa C2B confirmation & validation URLs (run once)'

    def handle(self, *args, **options):
        access_token = get_mpesa_access_token()
        ngrok_url = settings.NGROK_URL.rstrip('/')  # ensure no trailing slash issues
        shortcode = settings.MPESA_SHORTCODE  # put in settings: '174379' for sandbox

        api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v2/registerurl"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "ShortCode": shortcode,
            "ResponseType": "Completed",  # or "Cancelled" if you want to reject some
            "ConfirmationURL": f"{ngrok_url}/payments/confirmation/",
            "ValidationURL": f"{ngrok_url}/payments/validation/",
        }

        try:
            resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            self.stdout.write(self.style.SUCCESS(f"Registration success: {data}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed: {str(e)} → Response: {resp.text if 'resp' in locals() else 'No response'}"))