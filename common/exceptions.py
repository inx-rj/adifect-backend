from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_handle_exception(request, exc):
    response = exception_handler(exc, request)

    if not response:
        return Response({
            'error': True,
            'message': str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        response.data = {
            'error': True,
            'message': response.data
        }
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:

        response.data = {
            'error': True,
            'message': response.data['detail']
        }
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        response.data = {
            'error': True,
            'message': 'You do not have permission to perform this action.'
        }

    elif response.status_code == status.HTTP_404_NOT_FOUND:
        response.data = {
            'error': True,
            'message': 'Data not found.'
        }

    return response
