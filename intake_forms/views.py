import json

from django.db import transaction
from django.db.models import OuterRef
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, serializers
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from administrator.serializers import customUserSerializer
from authentication.models import CustomUser
from common.exceptions import custom_handle_exception
from common.pagination import CustomPagination
from intake_forms.constants import INTAKE_FORM_RETRIEVED_SUCCESSFULLY, INTAKE_FORM_CREATED_SUCCESSFULLY, \
    INTAKE_FORM_UPDATED_SUCCESSFULLY, INTAKE_FORM_SUBMIT_SUCCESS, INTAKE_FORM_TASK_CREATED_SUCCESSFULLY, \
    INTAKE_FORM_TASK_UPDATED_SUCCESSFULLY
from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormFieldVersion, IntakeFormSubmissions, FormTask, \
    FormTaskMapping
from intake_forms.serializers import IntakeFormSerializer, IntakeFormFieldSerializer, IntakeFormSubmitSerializer, \
    IntakeFormTaskSerializer, IntakeFormTaskMappingSerializer, FormTaskDetailSerializer


class IntakeFormListCreateView(generics.ListCreateAPIView):
    """
    View for creating intake form and view list of all intake form
    """

    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormSerializer
    queryset = IntakeForm.objects.filter().order_by('-id')
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['title', 'intake_form_field_version_form__user__username', 'created']
    ordering_fields = ['title', 'intake_form_field_version_form__user__username', 'created']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        API to get list of intake form
        """
        queryset = self.filter_queryset(self.get_queryset().annotate(
            intake_form_field_version_form__user__username=IntakeFormFieldVersion.objects.filter(
                intake_form_id=OuterRef('id')).values('user__username')[:1]))
        page = self.paginate_queryset(queryset)
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
    permission_classes = [IsAuthenticated]

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
        serializer = self.get_serializer(data=request.data, context={"fields": request.data.get('fields'),
                                                                     "user": request.user,
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

    permission_classes = [IsAuthenticated]

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
                                                                           "user": request.user,
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
    permission_classes = [IsAuthenticated]
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
        data["submitted_user"] = request.user.id
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
    ordering_fields = ['created', 'submitted_user__email', 'submitted_user__first_name']
    permission_classes = [IsAuthenticated]

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


class IntakeFormTaskListCreateView(generics.ListCreateAPIView):
    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormTaskSerializer
    queryset = FormTask.objects.filter(is_trashed=False).order_by('-id')
    filter_backends = [SearchFilter]
    search_fields = ['name']
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        self.queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({'data': response.data, 'message': ''})

    def post(self, request, *args, **kwargs):
        assign_to = request.data.pop('assign_to')
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()

            form_task_data = []
            for assign in assign_to:
                form_task_data.append({"form_task": instance.id, "assign_to": assign})

            form_task_map_serializer = IntakeFormTaskMappingSerializer(data=form_task_data, many=True)
            form_task_map_serializer.is_valid(raise_exception=True)
            form_task_map_serializer.save()
        return Response({'data': serializer.data, 'message': INTAKE_FORM_TASK_CREATED_SUCCESSFULLY},
                        status=status.HTTP_201_CREATED)


class IntakeFormTaskUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    def handle_exception(self, exc):
        return custom_handle_exception(request=self.request, exc=exc)

    serializer_class = IntakeFormTaskSerializer
    queryset = FormTask.objects.filter(is_trashed=False).order_by('-id')
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        if kwargs.get('id'):
            form_task_data = self.queryset.get(id=kwargs.get('id'))
            serializer = FormTaskDetailSerializer(form_task_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            if not request.data.get('assign_to'):
                raise serializers.ValidationError({"assign_to": "This Field is required!"})
            assign_to = request.data.pop('assign_to')
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            FormTaskMapping.objects.filter(form_task_id=instance.id).update(is_trashed=True)
            form_task_data = []
            for assign in assign_to:
                form_task_data.append({"form_task": instance.id, "assign_to": assign})

            form_task_map_serializer = IntakeFormTaskMappingSerializer(data=form_task_data, many=True)
            form_task_map_serializer.is_valid(raise_exception=True)
            form_task_map_serializer.save()
        return Response({'data': serializer.data, 'message': INTAKE_FORM_TASK_UPDATED_SUCCESSFULLY})

    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            form_task_instance = get_object_or_404(FormTask, id=kwargs.get('id'), is_trashed=False)
            form_task_map_instance = get_object_or_404(FormTaskMapping, form_task_id=kwargs.get('id'), is_trashed=False)

            instance = get_object_or_404(FormTask, id=kwargs.get('id'), is_trashed=False)
            form_task_instance.delete()
            form_task_map_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignUserListView(generics.ListAPIView):
    serializer_class = customUserSerializer
    queryset = CustomUser.objects.filter(is_trashed=False).order_by('-id')
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({'data': serializer.data, 'message': ''}, status=status.HTTP_200_OK)
