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

class IsAdminMember(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 3 and request.user.agency_level.filter(levels=1):
                return True

class IsMarketerMember(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 3 and request.user.agency_level.filter(levels=2):
                return True

class IsApproverMember(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.method in ['GET']:
            if request.user.role == 3 and request.user.agency_level.filter(levels=3):
                return True


class InHouseMember(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.role == 3 and request.user.agency_level.filter(levels=4):
                return True