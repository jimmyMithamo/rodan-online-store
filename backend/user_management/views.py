from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
import logging
from .models import User, ShippingAddress
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    ShippingAddressSerializer,
    CustomTokenObtainPairSerializer
)

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'list':
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    def create(self, request, *args, **kwargs):
        """Register a new user"""
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'success': True,
                    'message': 'User registered successfully',
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response({
                    'success': False,
                    'message': 'Registration failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.error(f"Database integrity error during user registration: {str(e)}")
            return Response({
                'success': False,
                'message': 'A user with this email already exists',
                'errors': {'email': ['This email is already registered']}
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred during registration',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user's profile"""
        try:
            serializer = self.get_serializer(request.user)
            return Response({
                'success': True,
                'user': serializer.data
            })
        except Exception as e:
            logger.error(f"Error retrieving user profile: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve user profile',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """Update current user's profile"""
        try:
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'user': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Profile update failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.error(f"Database integrity error during profile update: {str(e)}")
            return Response({
                'success': False,
                'message': 'Email already exists',
                'errors': {'email': ['This email is already taken']}
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during profile update: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred while updating profile',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ShippingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new shipping address"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                address = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Shipping address created successfully',
                    'address': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to create shipping address',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating shipping address: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred while creating address',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """Update a shipping address"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Shipping address updated successfully',
                    'address': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to update shipping address',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating shipping address: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred while updating address',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a shipping address"""
        try:
            instance = self.get_object()
            instance.delete()
            return Response({
                'success': True,
                'message': 'Shipping address deleted successfully'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error deleting shipping address: {str(e)}")
            return Response({
                'success': False,
                'message': 'An unexpected error occurred while deleting address',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def list(self, request, *args, **kwargs):
        """List user's shipping addresses"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'addresses': serializer.data,
                'count': queryset.count()
            })
        except Exception as e:
            logger.error(f"Error listing shipping addresses: {str(e)}")
            return Response({
                'success': False,
                'message': 'Unable to retrieve shipping addresses',
                'errors': {'non_field_errors': ['Please try again later']}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Custom login with better error handling"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    **serializer.validated_data
                }, status=status.HTTP_200_OK)
            else:
                errors = serializer.errors
                message = 'Login failed'
                # Specific error handling
                if 'non_field_errors' in errors:
                    error_text = errors['non_field_errors'][0]
                    if 'No active account found' in error_text:
                        message = 'Account not found or inactive'
                    elif 'Unable to log in with provided credentials' in error_text:
                        # Check if user exists
                        UserModel = get_user_model()
                        email = request.data.get('email')
                        user_exists = UserModel.objects.filter(email=email).exists()
                        if not user_exists:
                            message = 'Account not found'
                        else:
                            message = 'Incorrect password'
                    else:
                        message = error_text
                elif 'email' in errors:
                    message = 'Please provide a valid email address'
                elif 'password' in errors:
                    message = 'Password is required'
                return Response({
                    'success': False,
                    'message': message,
                    'errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except (InvalidToken, TokenError) as e:
            logger.error(f"JWT Token error during login: {str(e)}")
            # Handle JWT specific errors
            if 'No active account found' in str(e):
                UserModel = get_user_model()
                email = request.data.get('email')
                user_exists = UserModel.objects.filter(email=email).exists()
                if not user_exists:
                    message = 'Account not found, please register'
                else:
                    message = 'Account is inactive or credentials are incorrect'
            else:
                message = 'Invalid credentials'
            return Response({
                'success': False,
                'message': message,
                'errors': {'non_field_errors': [message]}
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            # Check if the error message contains authentication specific info
            error_str = str(e)
            if 'No active account found' in error_str:
                UserModel = get_user_model()
                email = request.data.get('email')
                user_exists = UserModel.objects.filter(email=email).exists()
                if not user_exists:
                    message = 'Account not found'
                else:
                    message = 'Account is inactive or credentials are incorrect'
                return Response({
                    'success': False,
                    'message': message,
                    'errors': {'non_field_errors': [message]}
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': 'An unexpected error occurred',
                    'errors': {'non_field_errors': ['Please try again later']}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
