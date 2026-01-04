from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from rest_framework import exceptions
from django.db.models import Q
from django.core.validators import RegexValidator 
User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims that HomePoint API will use
        token['user_id'] = user.id
        token['email'] = user.email
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        # Optional: add groups for role-based access later
        # token['groups'] = list(user.groups.values_list('name', flat=True))

        return token

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='customer')

    class Meta:
        model = User
        fields = ('username', 'email','phone_number', 'password', 'role', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_phone_number(self, value):
        value = value.strip()
        if value.startswith('0'):
            value = '+254' + value[1:]
        elif value.startswith('254'):
            value = '+' + value
        elif not value.startswith('+254'):
            raise serializers.ValidationError("Invalid Kenyan phone number format.")
        
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number already registered.")
        
        validator = RegexValidator(r'^\+254\d{9}$', 'Invalid format after normalization.')
        validator(value)
        return value

    def validate_role(self, value):
        if value not in dict(User.ROLE_CHOICES).keys():
            raise serializers.ValidationError("Invalid role.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email = validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            role=validated_data.get('role', 'customer'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_verified=False  # Require OTP verification
        )
        return user



class UserProfileSerializer(serializers.ModelSerializer):
    """For retrieving current user + role-specific profile"""
    fundi_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'phone_number', 'role', 'first_name', 'last_name', 
                  'is_verified', 'groups', 'fundi_profile')
        read_only_fields = ('phone_number', 'role')

    def get_fundi_profile(self, obj):
        if obj.role == 'fundi' and hasattr(obj, 'fundi_profile'):
            profile = obj.fundi_profile
            return {
                'trade': profile.trade,
                'location': profile.location,
                'whatsapp_contact': profile.whatsapp_contact,
                'bio': profile.bio,
                'rating': profile.rating,
                'is_approved': profile.is_approved,
                'is_complete': profile.is_complete
            }
        return None

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    # Method to  ensure old password is correct
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, data):
        """Ensure new_password and confirm_password match."""
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data
    
    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class UserDeleteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['password']
    # Method to compare passwords
    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect")
        return value
    
    # Method to delete user instance
    def delete(self, instance):
        instance.delete()
        return instance