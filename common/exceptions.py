from rest_framework.exceptions import ValidationError, PermissionDenied, \
    NotAuthenticated, NotFound, AuthenticationFailed
from rest_framework.views import exception_handler


def custom_handle_exception(request, exc):
    response = exception_handler(exc, request)

    if isinstance(exc, ValidationError):
        response.data = {
            'error': True,
            'message': response.data
        }
    elif isinstance(exc, NotAuthenticated):
        response.data = {
            'error': True,
            'message': 'Authentication credentials were not provided.'
        }
    elif isinstance(exc, AuthenticationFailed):
        response.data = {
            'error': True,
            'message': 'Incorrect authentication credentials.'
        }
    elif isinstance(exc, PermissionDenied):
        response.data = {
            'error': True,
            'message': 'You do not have permission to perform this action.'
        }

    elif isinstance(exc, NotFound):
        response.data = {
            'error': True,
            'message': 'Data not found.'
        }

    return response
