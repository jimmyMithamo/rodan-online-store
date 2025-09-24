from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error response format
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Log the error
        logger.error(f"API Error: {exc.__class__.__name__}: {str(exc)}")
        
        # Create custom error response
        custom_response_data = {
            'success': False,
            'message': 'An error occurred',
            'errors': {}
        }

        # Handle different types of errors
        if hasattr(response.data, 'items'):
            # DRF serializer errors
            custom_response_data['errors'] = response.data
            
            # Set appropriate message based on error type
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                custom_response_data['message'] = 'Validation error'
            elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                custom_response_data['message'] = 'Authentication required'
            elif response.status_code == status.HTTP_403_FORBIDDEN:
                custom_response_data['message'] = 'Permission denied'
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                custom_response_data['message'] = 'Resource not found'
            elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
                custom_response_data['message'] = 'Method not allowed'
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                custom_response_data['message'] = 'Too many requests'
            elif response.status_code >= 500:
                custom_response_data['message'] = 'Internal server error'
        else:
            # Handle string responses
            custom_response_data['errors'] = {'detail': response.data}

        response.data = custom_response_data

    return response