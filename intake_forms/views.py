import json

from django.db import transaction
from django.http import Http404
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
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['title', 'intake_form_field_version_form__user__username', 'created',
                     'intake_form_field_version_form__version']
    ordering_fields = ['title', 'intake_form_field_version_form__user__username', 'created',
                       'intake_form_field_version_form__version']
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
    lookup_field = 'form_slug'
    permission_classes = []

    def get(self, request, *args, **kwargs):
        """API to get intake form"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update intake form"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, context={'slug_name': self.kwargs.get('slug')})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive intake form"""
        instance = get_object_or_404(IntakeForm, form_slug=kwargs.get('slug'), is_trashed=False)
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
                                                                     "user": None,
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
        slug_name = self.kwargs.get('slug')

        if not self.request.GET.get('version'):
            intake_form_field_version = IntakeFormFieldVersion.objects.filter(
                intake_form__form_slug=slug_name, is_trashed=False)
            if not intake_form_field_version:
                raise Http404()
            form_version = intake_form_field_version.latest('id').id
        else:
            form_version_response = get_object_or_404(IntakeFormFieldVersion,
                                                      intake_form__form_slug=slug_name,
                                                      version=self.request.GET.get(
                                                          'version'), is_trashed=False)
            form_version = form_version_response.id

        intake_form_field_obj = IntakeFormFields.objects.filter(form_version=form_version, is_trashed=False)

        intake_form_data = IntakeForm.objects.filter(form_slug=slug_name).first()

        if not intake_form_field_obj:
            raise Http404()
        serializer = IntakeFormFieldSerializer(intake_form_field_obj, many=True)
        intake_serializer = IntakeFormSerializer(intake_form_data)
        data = {
            "data": serializer.data,
        }
        if intake_form_data:
            data["intake_form"] = intake_serializer.data

        return Response({'data': data, 'message': INTAKE_FORM_RETRIEVED_SUCCESSFULLY})

    def put(self, request, *args, **kwargs):
        """put request to update intake form field"""
        slug_name = self.kwargs.get('slug')

        intake_form_field_obj = IntakeFormFields.objects.filter(
            form_version__intake_form__form_slug=slug_name, is_trashed=False)
        if not intake_form_field_obj:
            raise Http404()
        intake_form_field_version_obj = IntakeFormFieldVersion.objects.filter(
            intake_form__form_slug=slug_name)

        serializer = IntakeFormFieldSerializer(data=request.data, context={"fields": request.data.get('fields'),
                                                                           "user": None,
                                                                           "intake_form": request.data.get(
                                                                               'intake_form'),
                                                                           "slug_name": slug_name,
                                                                           "intake_form_field": intake_form_field_obj,
                                                                           "intake_form_field_version_obj": intake_form_field_version_obj
                                                                           })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'data': "", 'message': INTAKE_FORM_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        """delete request to inactive intake form field"""
        intake_form_field_obj = IntakeFormFields.objects.filter(
            form_version__intake_form__uuid=self.kwargs.get('form_id'), is_trashed=False)
        if not intake_form_field_obj:
            raise Http404()
        if not (version := request.data.get('version')):
            raise serializers.ValidationError({"version": "This field is required!"})

        intake_form_field_version_obj = get_object_or_404(IntakeFormFieldVersion,
                                                          intake_form__uuid=kwargs.get('form_id'),
                                                          is_trashed=False, version=version)
        with transaction.atomic():
            intake_form_field_obj.update(is_trashed=True)
            intake_form_field_version_obj.delete()
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
        if not (form_version := IntakeFormFieldVersion.objects.filter(intake_form__form_slug=kwargs.get('slug'),
                                                                      is_trashed=False)):
            raise Http404()

        data = request.data
        data['form_version'] = form_version.latest('id').id
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
    ordering_fields = ['created', 'submitted_user__username']
    permission_classes = []

    def list(self, request, *args, **kwargs):

        if self.request.GET.get('version'):
            self.queryset = self.filter_queryset(self.get_queryset()).filter(
                form_version__intake_form__form_slug=kwargs.get('slug'),
                form_version__version=self.request.GET.get('version'))
        else:
            latest_form_version_subquery = IntakeFormFieldVersion.objects.filter(
                intake_form__form_slug=kwargs.get('slug'))

            if not latest_form_version_subquery:
                raise Http404()

            self.queryset = self.filter_queryset(self.get_queryset()).filter(
                form_version__intake_form__form_slug=kwargs.get('slug'),
                form_version__version=latest_form_version_subquery.latest('id').version)

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
        response = self.get_paginated_response(serializer.data)
        return Response({'data': response.data, 'message': ''},
                        status=status.HTTP_200_OK)
