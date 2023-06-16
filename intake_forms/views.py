import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, serializers
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import custom_handle_exception
from common.pagination import CustomPagination
from intake_forms.constants import INTAKE_FORM_RETRIEVED_SUCCESSFULLY, INTAKE_FORM_CREATED_SUCCESSFULLY, \
    INTAKE_FORM_UPDATED_SUCCESSFULLY, INTAKE_FORM_SUBMIT_SUCCESS
from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormFieldVersion, IntakeFormSubmissions
from intake_forms.serializers import IntakeFormSerializer, IntakeFormFieldSerializer, IntakeFormSubmitSerializer


class IntakeFormListCreateView(generics.ListCreateAPIView):
    """
    View for creating intake form and view list of all intake form
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormSerializer
    queryset = IntakeForm.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        API to get list of intake form
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """API to create intake form"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_CREATED_SUCCESSFULLY}, status=status.HTTP_201_CREATED)


class IntakeFormRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, update and delete intake form
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormSerializer
    queryset = IntakeForm.objects.filter(is_trashed=False).order_by('-id')
    lookup_field = 'id'
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """API to get intake form"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update intake form"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, context={'id': self.kwargs.get('id')})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive intake form"""
        instance = get_object_or_404(IntakeForm, pk=kwargs.get('id'), is_trashed=False)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IntakeFormFieldListCreateView(generics.ListCreateAPIView):
    """
    View for creating intake form field and view list of all intake form field
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormFieldSerializer
    queryset = IntakeFormFields.objects.filter(is_trashed=False).order_by('-id')
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['form_version__intake_form__title', 'field_name', 'field_type']
    ordering_fields = ['id', 'form_version__intake_form__title', 'field_type', 'field_name']
    pagination_class = CustomPagination
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """
        API to get list of intake form field
        """
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def post(self, request, *args, **kwargs):
        """API to create intake form field"""
        serializer = self.get_serializer(data=request.data, context={"fields": request.data.get('fields'),
                                                                     "user": self.request.user,
                                                                     "intake_form": request.data.get('intake_form')
                                                                     })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_CREATED_SUCCESSFULLY}, status=status.HTTP_201_CREATED)


class IntakeFormFieldRetrieveUpdateDeleteView(APIView):
    """
    View for retrieve, update and delete intake form field
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    permission_classes = []

    def get(self, request, *args, **kwargs):
        """API to get intake form field"""
        form_id = self.kwargs.get('form_id')
        try:
            version = float(self.kwargs.get('version_id'))
        except ValueError:
            raise serializers.ValidationError({"version_id": [f"expected a number but got {kwargs.get('version_id')}"]})

        intake_form_field_obj = IntakeFormFields.objects.filter(form_version__intake_form_id=form_id,
                                                                form_version__version=version, is_trashed=False)
        if not intake_form_field_obj:
            raise serializers.ValidationError(
                {"form_version": [
                    f"Invalid pk \"{self.kwargs.get('form_id')}\"\"{self.kwargs.get('version_id')}\" - object does not exist."]})
        serializer = IntakeFormFieldSerializer(intake_form_field_obj, many=True)

        return Response({'data': serializer.data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update intake form field"""
        try:
            version = float(self.kwargs.get('version_id'))
        except ValueError:
            raise serializers.ValidationError({"version_id": [f"expected a number but got {kwargs.get('version_id')}"]})

        intake_form_field_obj = IntakeFormFields.objects.filter(form_version__intake_form_id=self.kwargs.get('form_id'),
                                                                form_version__version=version, is_trashed=False)
        if not intake_form_field_obj:
            raise serializers.ValidationError('Data not found.')
        intake_form_field_version_obj = IntakeFormFieldVersion.objects.filter(intake_form_id=self.kwargs.get('form_id'),
                                                                              version=version)

        serializer = IntakeFormFieldSerializer(data=request.data, context={"fields": request.data.get('fields'),
                                                                           "user": self.request.user,
                                                                           "intake_form": request.data.get(
                                                                               'intake_form'),
                                                                           "id": self.kwargs.get('form_id'),
                                                                           "intake_form_field": intake_form_field_obj,
                                                                           "intake_form_field_version_obj": intake_form_field_version_obj
                                                                           })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive intake form field"""
        try:
            version = float(self.kwargs.get('version_id'))
        except ValueError:
            raise serializers.ValidationError({"version_id": [f"expected a number but got {kwargs.get('version_id')}"]})
        intake_form_field_obj = IntakeFormFields.objects.filter(form_version__intake_form_id=self.kwargs.get('form_id'),
                                                                form_version__version=version, is_trashed=False)
        if not intake_form_field_obj:
            raise serializers.ValidationError('Data not found.')
        intake_form_field_version_obj = IntakeFormFieldVersion.objects.filter(intake_form_id=self.kwargs.get('form_id'),
                                                                              version=version)
        with transaction.atomic():
            intake_form_field_obj.update(is_trashed=True)
            intake_form_field_version_obj.update(is_trashed=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IntakeFormSubmit(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    User Intake form submit API.
    """
    serializer_class = IntakeFormSubmitSerializer
    permission_classes = []
    queryset = IntakeFormSubmissions.objects.filter(is_trashed=False)
    lookup_field = 'id'

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    def post(self, request, *args, **kwargs):
        try:
            version_id = float(kwargs.get('version_id'))
        except ValueError:
            raise serializers.ValidationError({"version_id": [f"expected a number but got {kwargs.get('version_id')}"]})
        form_version = get_object_or_404(IntakeFormFieldVersion, intake_form_id=kwargs.get('form_id'),
                                         version=kwargs.get('version_id'), is_trashed=False)
        data = request.data
        data['form_version'] = form_version.id
        # data["submitted_user"] = request.user.id
        data["submitted_user"] = None
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': '', 'message': INTAKE_FORM_SUBMIT_SUCCESS}, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': ''}, status=status.HTTP_200_OK)


class ListIntakeFormSubmissions(generics.ListAPIView):
    """API to get form submissions with versions search filter"""

    serializer_class = IntakeFormSubmitSerializer
    pagination_class = CustomPagination
    queryset = IntakeFormSubmissions.objects.filter(is_trashed=False)
    filter_backends = [OrderingFilter]
    ordering = ['created', '-created', 'submitted_user', '-submitted_user']
    permission_classes = []

    def list(self, request, *args, **kwargs):
        try:
            version_id = float(kwargs.get('version_id'))
        except ValueError:
            raise serializers.ValidationError({"version_id": [f"expected a number but got {kwargs.get('version_id')}"]})

        self.queryset = self.filter_queryset(self.get_queryset()).filter(
            form_version__intake_form_id=kwargs.get('form_id'),
            form_version__version=kwargs.get('version_id'))

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': ''},
                            status=status.HTTP_200_OK)
