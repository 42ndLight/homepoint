from django.test import TestCase
from django.conf import settings
import requests
from rest_framework.test import APIClient
from payments.mpesa.utils import get_mpesa_access_token

class PaymentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Optional: if you want to mock auth or setup test order
        self.shortcode = "600977"  # Sandbox default from portal
        self.test_phone = "254708374149"
        self.bill_ref = "TEST-HP-12346"  # Your order ref format
        self.amount = "1030"  # As in your example

    def test_simulate_c2b_payment(self):
        """Simulate a C2B payment to trigger confirmation callback."""
        try:
            access_token = get_mpesa_access_token()
            self.assertTrue(access_token, "Failed to get access token")
        except Exception as e:
            self.fail(f"Token fetch failed: {str(e)}")

        url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate"

        payload = {
            "ShortCode": self.shortcode,
            "CommandID": "CustomerPayBillOnline",  # For PayBill
            "Amount": self.amount,
            "Msisdn": self.test_phone,
            "BillRefNumber": self.bill_ref  # This should appear in callback as BillRefNumber
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()  # Fail if not 200

            data = response.json()
            print("Simulation response:", data)  # For console debug

            # Expected success response (sandbox):
            # {"ConversationID": "...", "OriginatorConversationID": "...", "ResponseDescription": "Accept the service request successfully."}
            self.assertIn("ResponseDescription", data)
            self.assertEqual(data.get("ResponseDescription"), "Accept the service request successfully.")

            print(f"Simulation sent successfully for ref {self.bill_ref}. Wait 30-120s and check logs for callback.")
        except requests.exceptions.RequestException as e:
            self.fail(f"Simulation failed: {str(e)} - Response: {response.text if 'response' in locals() else 'No response'}")