from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.cache import cache
import logging

from .serializers import (
    RegisterSerializer, CustomTokenObtainPairSerializer,
    UserProfileSerializer, UpdateProfileSerializer,
    ChangePasswordSerializer, UserDeleteSerializer,
    PasswordResetSerializer
)
from .utils import generate_and_send_otp
from .permissions import IsAdminRole
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


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
        phone_number = request.data.get('phone_number')
        try:
            user = User.objects.get(phone_number=phone_number)
            generate_and_send_otp(user.phone_number, intent="reset")
            logger.info(f"Password reset OTP initiated for phone: {phone_number}")
        except User.DoesNotExist:
            pass # Silently fail
            
        return Response({"message": "If the phone number is registered, a password reset OTP was sent."})

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        provided_otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        cache_key = f"reset_otp_{phone_number}"
        cached_otp = cache.get(cache_key)
        
        if not cached_otp or cached_otp != provided_otp:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(phone_number=phone_number)
            user.set_password(new_password)
            user.save()
            
            cache.delete(cache_key)
            logger.info(f"User {user.username} successfully reset password via OTP.")
            return Response({"message": "Password updated successfully."})
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

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