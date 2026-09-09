from django.urls import path
from .views import (
    RegisterView, UserProfileView,
    UpdateProfileView, LogoutView, 
    ChangePasswordView, DeleteProfileView,
    LoginInitiateView, LoginVerifyOTPView,
    PasswordResetRequestView, PasswordResetVerifyOTPView,
    PasswordResetConfirmView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('auth/profile/update/', UpdateProfileView.as_view(), name='profile_update'),
    path('auth/profile/update/password/', ChangePasswordView.as_view(), name='profile-update-pass'),
    path('auth/profile/delete/', DeleteProfileView.as_view(), name='profile_delete'),
    
    # OTP Login & Password Reset routes
    path('auth/token/', LoginInitiateView.as_view(), name='token_obtain_pair'),
    path('auth/token/verify-otp/', LoginVerifyOTPView.as_view(), name='token_verify_otp'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/verify-otp/', PasswordResetVerifyOTPView.as_view(), name='password_reset_verify_otp'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]