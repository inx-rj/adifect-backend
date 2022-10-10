from django.db import models
from rest_framework import permissions



class SoftDeleteManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.with_deleted = kwargs.pop('deleted', False)
        super(SoftDeleteManager, self).__init__(*args, **kwargs)

    def _base_queryset(self):
        return super().get_queryset()

    def get_queryset(self):
        qs = self._base_queryset()
        if self.with_deleted:
            return qs
        return qs.filter(is_trashed=False)





class IsAdmin(permissions.BasePermission):
    # edit_methods = ("PUT", "PATCH","GET","POST")

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 0:
                return True

class IsAgency(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 2:
                return True


class IsCreator(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 1:
                return True


