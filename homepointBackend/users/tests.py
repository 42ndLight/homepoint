from unittest.mock import patch
from urllib.parse import urlencode

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient

from .models import SmsNotification, User
from .utils import generate_and_send_otp, get_otp_cache_key, send_at_sms


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


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='staff-user',
            email='staff@example.com',
            phone_number='+254700000002',
            password='password',
            role='staff',
        )

    def test_staff_login_issues_tokens_without_otp(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': self.user.username, 'password': 'password'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertFalse(
            cache.get(get_otp_cache_key('login', self.user.phone_number))
        )


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='profile-user',
            email='profile@example.com',
            phone_number='+254700000004',
            password='password',
        )
        self.client.force_authenticate(self.user)

    def test_user_can_update_identity_and_contact_details(self):
        response = self.client.patch(
            reverse('profile_update'),
            {
                'username': 'updated-user',
                'email': 'updated@example.com',
                'phone_number': '0712345678',
                'first_name': 'Updated',
                'last_name': 'User',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'updated-user')
        self.assertEqual(response.data['email'], 'updated@example.com')
        self.assertEqual(response.data['phone_number'], '+254712345678')
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updated-user')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.phone_number, '+254712345678')


class StaffManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            phone_number='+254700000001',
            password='password',
            role='admin',
        )
        self.staff = User.objects.create_user(
            username='staff-user',
            email='staff@example.com',
            phone_number='+254700000002',
            password='password',
            role='staff',
        )
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            phone_number='+254700000003',
            password='password',
            role='customer',
        )

    def test_admin_can_list_staff_only(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse('staff_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([user['id'] for user in response.data], [self.staff.id])

    def test_non_admin_cannot_list_or_delete_staff(self):
        self.client.force_authenticate(self.staff)

        self.assertEqual(self.client.get(reverse('staff_list')).status_code, 403)
        self.assertEqual(
            self.client.delete(reverse('staff_delete', args=[self.staff.id])).status_code,
            403,
        )
        self.assertTrue(User.objects.filter(pk=self.staff.id).exists())

    def test_admin_can_delete_staff_but_not_non_staff(self):
        self.client.force_authenticate(self.admin)

        self.assertEqual(
            self.client.delete(reverse('staff_delete', args=[self.staff.id])).status_code,
            204,
        )
        self.assertFalse(User.objects.filter(pk=self.staff.id).exists())
        self.assertEqual(
            self.client.delete(reverse('staff_delete', args=[self.customer.id])).status_code,
            404,
        )


class AfricaTalkingSmsTests(TestCase):
    @override_settings(AT_API_KEY='test-key', AT_USERNAME='sandbox')
    @patch('users.utils.requests.post')
    def test_send_creates_notification_for_provider_message(self, mock_post):
        mock_post.return_value.json.return_value = {
            'SMSMessageData': {
                'Recipients': [{
                    'number': '+254712345678',
                    'messageId': 'ATX-123',
                    'status': 'Success',
                }]
            }
        }

        self.assertTrue(
            send_at_sms(
                '+254712345678',
                'Your HomePoint code is 123456.',
                intent='login',
            )
        )

        notification = SmsNotification.objects.get(provider_message_id='ATX-123')
        self.assertEqual(notification.recipient, '+254712345678')
        self.assertEqual(notification.intent, 'login')
        self.assertEqual(notification.status, 'PENDING')
        self.assertEqual(
            notification.response_metadata['SMSMessageData']['Recipients'][0]['messageId'],
            'ATX-123',
        )


class SmsDeliveryReportCallbackTests(TestCase):
    url = reverse('sms-dlr-callback')

    def post_callback(self, data):
        return self.client.post(
            self.url,
            urlencode(data),
            content_type='application/x-www-form-urlencoded',
        )

    def test_valid_callback_updates_matching_notification(self):
        notification = SmsNotification.objects.create(
            provider_message_id='ATX-123',
            recipient='+254700000000',
        )

        response = self.post_callback({
            'id': 'ATX-123',
            'status': 'Delivered',
            'phoneNumber': '+254712345678',
            'networkCode': '63902',
            'retryCount': '2',
        })

        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertEqual(notification.recipient, '+254712345678')
        self.assertEqual(notification.status, 'Delivered')
        self.assertEqual(notification.network_code, '63902')
        self.assertEqual(notification.retry_count, 2)
        self.assertIsNotNone(notification.delivery_reported_at)

    def test_duplicate_callback_is_idempotent(self):
        notification = SmsNotification.objects.create(
            provider_message_id='ATX-duplicate',
            recipient='+254700000000',
        )
        report = {
            'id': 'ATX-duplicate',
            'status': 'Failed',
            'phoneNumber': '+254712345678',
            'failureReason': 'Insufficient credit',
            'retryCount': '1',
        }

        self.assertEqual(self.post_callback(report).status_code, 200)
        self.assertEqual(self.post_callback(report).status_code, 200)
        notification.refresh_from_db()
        self.assertEqual(SmsNotification.objects.count(), 1)
        self.assertEqual(notification.status, 'Failed')
        self.assertEqual(notification.failure_reason, 'Insufficient credit')
        self.assertEqual(notification.retry_count, 1)

    def test_unknown_callback_is_accepted(self):
        with self.assertLogs('users.views', level='WARNING'):
            response = self.post_callback({
                'id': 'ATX-unknown',
                'status': 'Delivered',
                'phoneNumber': '+254712345678',
            })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SmsNotification.objects.exists())


class PurgeSmsNotificationsCommandTests(TestCase):
    def test_purges_notifications_older_than_ninety_days(self):
        expired = SmsNotification.objects.create(
            provider_message_id='ATX-expired',
            recipient='+254700000000',
        )
        SmsNotification.objects.filter(pk=expired.pk).update(
            created_at=timezone.now() - timedelta(days=91)
        )
        retained = SmsNotification.objects.create(
            provider_message_id='ATX-retained',
            recipient='+254700000000',
        )

        call_command('purge_sms_notifications')

        self.assertFalse(SmsNotification.objects.filter(pk=expired.pk).exists())
        self.assertTrue(SmsNotification.objects.filter(pk=retained.pk).exists())

    def test_malformed_callback_is_accepted(self):
        with self.assertLogs('users.views', level='WARNING'):
            response = self.post_callback({
                'id': 'ATX-malformed',
                'status': 'Delivered',
            })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SmsNotification.objects.exists())
