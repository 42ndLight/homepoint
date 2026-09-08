from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from .utils import generate_and_send_otp, get_otp_cache_key


class OTPGenerationTests(TestCase):
    phone_number = "+254712345678"

    def tearDown(self):
        cache.clear()

    @patch("users.utils.send_at_sms", return_value=True)
    @patch("users.utils.secrets.randbelow", return_value=7)
    def test_generates_and_caches_zero_padded_csprng_otp(
        self, mock_randbelow, mock_send_at_sms
    ):
        generate_and_send_otp(self.phone_number, intent="reset")

        mock_randbelow.assert_called_once_with(1_000_000)
        self.assertEqual(cache.get(get_otp_cache_key("reset", self.phone_number)), "000007")
        mock_send_at_sms.assert_called_once()

    @patch("users.utils.send_at_sms", return_value=True)
    @patch("users.utils.secrets.randbelow", return_value=999999)
    def test_generates_six_digit_otp_at_upper_bound(
        self, mock_randbelow, mock_send_at_sms
    ):
        generate_and_send_otp(self.phone_number, intent="login")

        self.assertEqual(cache.get(get_otp_cache_key("login", self.phone_number)), "999999")

# Create your tests here.
