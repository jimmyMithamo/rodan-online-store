from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
import re
from .models import User, ShippingAddress

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phonenumber = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'phonenumber', 'first_name', 'last_name', 'password', 'password_confirm')

    def validate_email(self, value):
        """Validate email format and uniqueness"""
        if not value:
            raise serializers.ValidationError("Email is required")
        
        # Check email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Please enter a valid email address")
        
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        return value.lower()

    def validate_phonenumber(self, value):
        """Validate phone number format if provided"""
        if not value:
            return ""
        # Remove spaces and special characters
        cleaned_phone = re.sub(r'[^-9+]', '', value)
        phone_regex = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_regex, cleaned_phone):
            raise serializers.ValidationError("Please enter a valid phone number")
        return cleaned_phone

    def validate_first_name(self, value):
        """Validate first name if provided"""
        if not value or not value.strip():
            return ""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long")
        return value.strip().title()

    def validate_last_name(self, value):
        """Validate last name if provided"""
        if not value or not value.strip():
            return ""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long")
        return value.strip().title()

    def validate_password(self, value):
        """Validate password strength"""
        if not value:
            raise serializers.ValidationError("Password is required")
        
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        # Check for at least one digit
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number")
        
        # Check for at least one letter
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("Password must contain at least one letter")
        
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': ["Passwords don't match"]
            })
        
        return attrs

    def create(self, validated_data):
        """Create user with proper error handling"""
        try:
            validated_data.pop('password_confirm')
            user = User.objects.create_user(**validated_data)
            return user
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': ["Failed to create user. Please try again."]
            })

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'phonenumber', 'first_name', 'is_staff', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')

    def validate_email(self, value):
        """Validate email format and uniqueness for updates"""
        if not value:
            raise serializers.ValidationError("Email is required")
        
        # Check email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Please enter a valid email address")
        
        # Check if email already exists (excluding current user)
        if self.instance and User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this email already exists")
        elif not self.instance and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        
        return value.lower()

    def validate_phonenumber(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        
        # Remove spaces and special characters
        cleaned_phone = re.sub(r'[^\d+]', '', value)
        
        # Basic phone number validation
        phone_regex = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_regex, cleaned_phone):
            raise serializers.ValidationError("Please enter a valid phone number")
        
        return cleaned_phone

    def validate_first_name(self, value):
        """Validate first name"""
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long")
        
        return value.strip().title()

    def validate_last_name(self, value):
        """Validate last name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long")
        
        return value.strip().title()

class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ('id', 'address', 'default_address', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_address(self, value):
        """Validate address field"""
        if not value or not value.strip():
            raise serializers.ValidationError("Address is required")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Address must be at least 10 characters long")
        
        return value.strip()

    def create(self, validated_data):
        """Create shipping address with proper error handling"""
        try:
            validated_data['user'] = self.context['request'].user
            
            # If this is set as default, unset other default addresses
            if validated_data.get('default_address', False):
                ShippingAddress.objects.filter(
                    user=validated_data['user'], 
                    default_address=True
                ).update(default_address=False)
            
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': ["Failed to create shipping address. Please try again."]
            })

    def update(self, instance, validated_data):
        """Update shipping address with proper error handling"""
        try:
            # If this is set as default, unset other default addresses
            if validated_data.get('default_address', False):
                ShippingAddress.objects.filter(
                    user=instance.user, 
                    default_address=True
                ).exclude(id=instance.id).update(default_address=False)
            
            return super().update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': ["Failed to update shipping address. Please try again."]
            })

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField()
        self.fields['password'] = serializers.CharField()
        # Remove the username field since we're using email
        if 'username' in self.fields:
            del self.fields['username']

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims if needed
        token['email'] = user.email
        return token
    
    def validate(self, attrs):
        """Custom validation with better error messages"""
        # Map email to username for the parent class
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email:
            raise serializers.ValidationError({
                'email': 'Email is required'
            })
        
        if not password:
            raise serializers.ValidationError({
                'password': 'Password is required'
            })
        
        # Set username to email for parent validation
        attrs['username'] = email
        
        try:
            data = super().validate(attrs)
        except serializers.ValidationError as e:
            # Handle authentication errors with better messages
            if 'non_field_errors' in e.detail:
                error_message = str(e.detail['non_field_errors'][0])
                
                # Check if user exists to provide more specific error
                try:
                    user_exists = User.objects.filter(email=email).exists()
                    if not user_exists:
                        raise serializers.ValidationError({
                            'non_field_errors': ['Account not found with this email address']
                        })
                    else:
                        # User exists but credentials are wrong
                        user = User.objects.filter(email=email).first()
                        if not user.is_active:
                            raise serializers.ValidationError({
                                'non_field_errors': ['Account is inactive. Please contact support.']
                            })
                        else:
                            raise serializers.ValidationError({
                                'non_field_errors': ['Incorrect password']
                            })
                except User.DoesNotExist:
                    raise serializers.ValidationError({
                        'non_field_errors': ['Account not found with this email address']
                    })
            raise e
        
        # Add user data to the response
        try:
            data.update({
                'user': UserSerializer(self.user).data
            })
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': ['Failed to retrieve user data']
            })
        
        return data