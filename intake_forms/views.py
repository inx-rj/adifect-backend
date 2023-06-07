from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import custom_handle_exception
from common.pagination import CustomPagination
from intake_forms.constants import INTAKE_FORM_RETRIEVED_SUCCESSFULLY, INTAKE_FORM_CREATED_SUCCESSFULLY, \
    INTAKE_FORM_UPDATED_SUCCESSFULLY
from intake_forms.models import IntakeForm, IntakeFormFields
from intake_forms.serializers import IntakeFormSerializer, IntakeFormFieldSerializer


class IntakeFormListCreateView(generics.ListCreateAPIView):
    """
    View for creating intake form and view list of all intake form
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormSerializer
    queryset = IntakeForm.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """API to get intake form"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update intake form"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
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
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

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
        if request.data.get('intake_form'):
            intake_form_field_obj = IntakeFormFields.objects.filter(
                intake_form=request.data.get('intake_form')).order_by('-version').first()
            version = intake_form_field_obj.version + 1 if intake_form_field_obj and intake_form_field_obj.version else 1
            request.data['version'] = version
        serializer = self.get_serializer(data=request.data, context={"fields": request.data.get('fields')})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_CREATED_SUCCESSFULLY}, status=status.HTTP_201_CREATED)
