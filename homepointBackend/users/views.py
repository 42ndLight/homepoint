from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging

from .serializers import (
    RegisterSerializer, CustomTokenObtainPairSerializer,
    UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, UserDeleteSerializer,
    PasswordResetSerializer, PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer, SmsDeliveryReportSerializer
)
from .models import SmsNotification
from .utils import (
    generate_and_send_otp, OTPCooldownError, RESET_RESEND_COOLDOWN,
    get_otp_cache_key, get_otp_cooldown_key,
    create_reset_grant, get_reset_grant_phone, delete_reset_grant
)
from .permissions import IsAdminRole
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class SmsDeliveryReportCallbackView(APIView):
    """Accept and apply an Africa's Talking SMS delivery report."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SmsDeliveryReportSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Malformed SMS delivery report: %s", serializer.errors)
            return Response({'status': 'accepted'}, status=status.HTTP_200_OK)

        report = serializer.validated_data
        try:
            with transaction.atomic():
                notification = (
                    SmsNotification.objects.select_for_update()
                    .filter(provider_message_id=report['id'])
                    .first()
                )
                if notification is None:
                    logger.warning(
                        "SMS delivery report received for unknown provider message ID %s",
                        report['id'],
                    )
                else:
                    updates = {
                        'recipient': report['phoneNumber'],
                        'status': report['status'],
                    }
                    if 'networkCode' in report:
                        updates['network_code'] = report['networkCode']
                    if 'failureReason' in report:
                        updates['failure_reason'] = report['failureReason']
                    if 'retryCount' in report:
                        updates['retry_count'] = report['retryCount']

                    if any(
                        getattr(notification, field) != value
                        for field, value in updates.items()
                    ):
                        for field, value in updates.items():
                            setattr(notification, field, value)
                        notification.delivery_reported_at = timezone.now()
                        notification.save()
        except Exception:
            logger.exception(
                "Internal error while processing SMS delivery report for %s", report['id']
            )

        return Response({'status': 'accepted'}, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [IsAdminRole]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info(f"Admin registered new user: {user.username} (Role: {user.role})")
        return Response({
            'user': UserProfileSerializer(user).data,
            'message': 'Registration successful. User must verify phone via OTP at login.'
        }, status=status.HTTP_201_CREATED)


class LoginInitiateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            
        if user.role in ['admin', 'staff']:
            # Trigger Africa's Talking OTP
            generate_and_send_otp(user.phone_number, intent="login")
            logger.info(f"OTP initiated for {user.username} (role: {user.role})")
            return Response({
                "message": "OTP sent to registered phone number.",
                "phone_number": user.phone_number,
                "requires_otp": True
            })
            
        # For non-admin/staff users, issue JWT immediately
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logger.info(f"User {user.username} logged in without OTP.")
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class LoginVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        provided_otp = request.data.get('otp')
        
        cache_key = f"login_otp_{phone_number}"
        cached_otp = cache.get(cache_key)
        
        if not cached_otp or cached_otp != provided_otp:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
            
        # OTP is valid, clear it
        cache.delete(cache_key)
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        refresh = RefreshToken.for_user(user)
        logger.info(f"User {user.username} verified OTP and logged in.")
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data
        })

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": "Phone number is not registered."}, status=status.HTTP_404_NOT_FOUND)

        try:
            generate_and_send_otp(user.phone_number, intent="reset", cooldown_seconds=RESET_RESEND_COOLDOWN)
        except OTPCooldownError as exc:
            return Response({
                "error": "An OTP was already sent recently. Please wait before requesting another.",
                "retry_after": exc.remaining_seconds,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        logger.info(f"Password reset OTP initiated for phone: {phone_number}")
        return Response({
            "message": "Password reset OTP sent.",
            "retry_after": RESET_RESEND_COOLDOWN,
        })

class PasswordResetVerifyOTPView(APIView):
    """
    Verifies the reset OTP only — does not touch the password. On success,
    issues a short-lived opaque reset_token the frontend uses to set a new
    password without carrying the phone number or OTP forward.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data['phone_number']
        provided_otp = serializer.validated_data['otp']

        cache_key = get_otp_cache_key('reset', phone_number)
        cached_otp = cache.get(cache_key)

        if not cached_otp or cached_otp != provided_otp:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # OTP is single-use — consume it immediately so it can't be replayed.
        cache.delete(cache_key)

        reset_token = create_reset_grant(phone_number)
        logger.info(f"Password reset OTP verified for phone: {phone_number}")
        return Response({
            "message": "OTP verified. You may now set a new password.",
            "reset_token": reset_token,
        })

class PasswordResetConfirmView(APIView):
    """Sets the new password using a reset_token issued by PasswordResetVerifyOTPView."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        phone_number = get_reset_grant_phone(reset_token)
        if not phone_number:
            return Response(
                {"error": "Reset session has expired. Please verify your OTP again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        # Clean up every cache artifact from this reset session.
        cache.delete(get_otp_cache_key('reset', phone_number))
        cache.delete(get_otp_cooldown_key('reset', phone_number))
        delete_reset_grant(reset_token)

        logger.info(f"User {user.username} successfully reset password via OTP.")
        return Response({"message": "Password updated successfully."})

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)



    
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_object()
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
    
class DeleteProfileView(generics.DestroyAPIView):
    serializer_class = UserDeleteSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        return self.request.user
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.delete()
        return Response({"message": "Account deleted successfully"}, status=status.HTTP_204_NO_CONTENT)