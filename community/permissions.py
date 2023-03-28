from rest_framework.permissions import DjangoModelPermissions


class IsAuthorizedForListCreate(DjangoModelPermissions):
    """
    Custom Permission to check if user is authorized according to their role
    """

    def has_permission(self, request, view):
        """
        To check if user has permission for the assigned role
        """
        return request.user.role == 2
