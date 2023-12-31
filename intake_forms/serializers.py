import os
import urllib
import uuid
from datetime import datetime

import boto3
import botocore.exceptions
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from administrator.serializers import customUserSerializer
from authentication.models import CustomUser
from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormFieldVersion, IntakeFormSubmissions, FormTask, \
    FormTaskMapping


class IntakeFormSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form
    """

    class Meta:
        model = IntakeForm
        fields = '__all__'

    def validate_title(self, value):
        if self.context.get('id'):
            if IntakeForm.objects.exclude(form_slug=self.context.get('slug_name')).filter(title=value,
                                                                                          is_trashed=False).exists():
                raise serializers.ValidationError("Title already exists.")
        elif IntakeForm.objects.filter(title=value, is_trashed=False).exists():
            raise serializers.ValidationError("Title already exists.")
        return value

    def to_representation(self, instance):
        rep = super(IntakeFormSerializer, self).to_representation(instance)
        if instance.intake_form_field_version_form and instance.intake_form_field_version_form.first():
            form_version_obj = instance.intake_form_field_version_form.first()
            form_versions = instance.intake_form_field_version_form.all()
            rep['max_version'] = form_versions.aggregate(Max('version'))['version__max']
            rep['version'] = [form_version.version for form_version in form_versions]
            rep['created_by'] = form_version_obj.user.username
            rep['responses'] = IntakeFormSubmissions.objects.filter(form_version__intake_form=instance).count()
        else:
            rep['max_version'] = 1.0
            rep['version'] = [1.0]
            rep['responses'] = 0
        return rep


class IntakeFormFieldVersionSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form field
    """

    class Meta:
        model = IntakeFormFieldVersion
        exclude = ['intake_form']


class IntakeFormFieldSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form field serializer
    """
    # intake_form = IntakeFormSerializer(write_only=True)
    form_version_data = serializers.SerializerMethodField()
    version = serializers.FloatField(required=False)
    field_name = serializers.CharField(required=False)
    field_type = serializers.CharField(required=False)

    class Meta:
        model = IntakeFormFields
        fields = '__all__'

    def get_form_version_data(self, obj):
        return IntakeFormFieldVersionSerializer(instance=obj.form_version).data

    def validate(self, attrs):
        fields_data = self.context.get("fields", [])
        if not fields_data:
            raise ValidationError({"fields": ["This field is required!"]})

        for field in fields_data:
            if not field.get('field_name'):
                raise serializers.ValidationError({"field_name": ["This field is required!"]})

            field_type = field.get('field_type')
            if not field_type:
                raise serializers.ValidationError({"field_type": ["This field is required!"]})

            if field_type in ['options', 'radio', 'options_multiple', 'radio_multiple', 'checkbox', 'checkbox_multiple',
                              'Dropdown', 'Multi-Select Dropdown', 'Radio Button'] and not field.get('options'):
                raise serializers.ValidationError({"options": ["Please give options!"]})

        if not self.context.get('slug_name'):
            if IntakeForm.objects.filter(
                    title=self.context.get('intake_form').get('title')).exists():
                raise serializers.ValidationError({"intake_form": "Form with this title already exists."})

        return attrs

    def create(self, validated_data):
        fields_data = self.context.get("fields", [])
        with transaction.atomic():
            if self.context.get('slug_name'):
                intake_form_obj = IntakeForm.objects.get(form_slug=self.context.get('slug_name'))
                # self.context.get('intake_form_field').update(is_trashed=True)
                # self.context.get('intake_form_field_version_obj').update(is_trashed=True)
            else:
                intake_form_obj = IntakeForm.objects.create(title=self.context.get('intake_form').get('title'))

            intake_form_field_version_obj = IntakeFormFieldVersion.objects.filter(
                intake_form_id=intake_form_obj.id).order_by('-version').first()
            version = intake_form_field_version_obj.version + 1 if intake_form_field_version_obj and intake_form_field_version_obj.version else 1
            form_version_obj = IntakeFormFieldVersion.objects.create(intake_form_id=intake_form_obj.id,
                                                                     version=version, user=self.context.get('user'))
            for field in fields_data:
                field['form_version'] = form_version_obj
                try:
                    IntakeFormFields(**field).full_clean()
                except ValidationError as e:
                    raise serializers.ValidationError(e.message_dict) from e

                field['field_name'] = field.get('field_name', "").strip()
                field['field_type'] = field.get('field_type', "").strip()
                IntakeFormFields.objects.create(**field)
        return True


class IntakeFormFieldsSubmitSerializer(serializers.Serializer):
    field_name = serializers.CharField(required=True)
    field_type = serializers.CharField(required=True)
    field_value = serializers.JSONField(required=True, allow_null=False)

    def validate_field_value(self, value):
        if value is None or value:
            return value
        else:
            raise serializers.ValidationError("This field may not be blank.")

    @staticmethod
    def is_valid_date(date_string):
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate(self, data):
        # if not data.get('field_value'):
        #     raise serializers.ValidationError({data.get('field_name'): [f"{data.get('field_name')} is required"]})

        if data.get("field_type") in ['text', 'Short Answer'] and len(data.get("field_value")) > 500:
            raise serializers.ValidationError({f"{data.get('field_name')}": "Limit 500 characters"})
        elif data.get("field_type") in ['date_picker', 'Date']:
            if not data.get("field_value").get("startDate"):
                raise serializers.ValidationError({"field_value": {"startDate": ["This field is required!"]}})
            if not self.is_valid_date(date_string=data.get("field_value").get("startDate")):
                raise serializers.ValidationError({f"{data.get('field_name')}": "Invalid date!"})
        elif data.get("field_type") in ['date_range_picker', 'Date Range']:
            if not data.get("field_value").get("startDate"):
                raise serializers.ValidationError({"field_value": {"startDate": ["This field is required!"]}})
            if not data.get("field_value").get("endDate"):
                raise serializers.ValidationError({"field_value": {"endDate": ["This field is required!"]}})
            if not self.is_valid_date(date_string=data.get("field_value").get("startDate")) and not self.is_valid_date(
                    date_string=data.get("field_value").get("endDate")):
                raise serializers.ValidationError({f"{data.get('field_name')}": "Invalid date range!"})

        # if data.get("field_type") == "Upload Attachment":
        #     if not self.context.get('files').get(data.get("field_value")):
        #         raise serializers.ValidationError(
        #             {f"{data.get('field_name')}": "File attachment not found for this field."})
        #     data["field_value"] = self.context.get('files').get(data.get("field_value"))

        return data


class IntakeFormSubmitSerializer(serializers.ModelSerializer):
    form_version = serializers.PrimaryKeyRelatedField(required=True,
                                                      queryset=IntakeFormFieldVersion.objects.filter(is_trashed=False))
    submitted_user = serializers.PrimaryKeyRelatedField(write_only=True,
                                                        queryset=CustomUser.objects.filter(is_trashed=False))
    fields = IntakeFormFieldsSubmitSerializer(many=True, required=True, write_only=True)
    submission_data = serializers.JSONField(read_only=True)

    class Meta:
        model = IntakeFormSubmissions
        fields = ['id', 'form_version', 'submitted_user', 'fields', 'submission_data', 'created']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # representation['submitted_by_user'] = instance.submitted_user.username
        representation['submitted_user__first_name'] = instance.submitted_user.get_full_name()
        representation['submitted_user__email'] = instance.submitted_user.email
        representation['form'] = instance.form_version.intake_form.title
        representation['form_slug'] = instance.form_version.intake_form.form_slug

        representation['max_version'] = instance.form_version.version == max(list(
            IntakeFormFieldVersion.objects.filter(intake_form=instance.form_version.intake_form,
                                                  is_trashed=False).values_list('version', flat=True)))

        return representation

    def validate(self, attrs):
        form_field_set = set(IntakeFormFields.objects.filter(form_version=attrs.get("form_version")
                                                             ).values_list('field_name', flat=True))
        submit_form_field_set = set()
        for field in attrs.get("fields"):
            if not IntakeFormFields.objects.filter(form_version=attrs.get("form_version"),
                                                   field_name=field.get("field_name", "").strip(),
                                                   field_type=field.get("field_type", "").strip()).exists():
                raise serializers.ValidationError(
                    {"field": f"Invalid field with field_name => {field.get('field_name', '').strip()}"
                              f" or field_type => {field.get('field_type', '').strip()}"})

            submit_form_field_set.add(field.get("field_name", "").strip())

        if form_field_set - submit_form_field_set:
            for field in form_field_set - submit_form_field_set:
                raise serializers.ValidationError({f"{field}": "This field is required."})

        return attrs

    @staticmethod
    def upload_file_s3(image_str):
        try:
            file_ext = image_str.split(";")[0].split('/')[-1]
            file_name = f'{uuid.uuid4()}.{file_ext}'

            # Retrieve the image content from the URL
            response = urllib.request.urlopen(image_str)
            with open(file_name, "wb") as file_obj:
                # Write the image content to the file object
                file_obj.write(response.read())

            with open(file_name, 'rb') as file:
                # Save the file to S3 using the default storage backend
                f = default_storage.save(f'intake_form_attachments/{file_name}', file)

            os.remove(file_name)
            return default_storage.url(f)

        except Exception as err:
            print(err)
            return ""

    def create(self, validated_data):
        for field in validated_data.get("fields"):
            if field.get('field_type').strip() in ["file", "Upload Attachment"]:
                field['field_value'] = self.upload_file_s3(image_str=field.get('field_value'))
        validated_data["submission_data"] = validated_data.pop("fields")
        return IntakeFormSubmissions.objects.create(**validated_data)


class FormSubmissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntakeFormSubmissions
        fields = ['id', 'form_version', 'submitted_user', 'submission_data', 'created']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['submitted_user'] = customUserSerializer(instance.submitted_user, read_only=True).data
        return representation


class IntakeFormTaskSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form
    """

    class Meta:
        model = FormTask
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['form_task_users'] = IntakeFormTaskMappingSerializer(
            FormTaskMapping.objects.filter(form_task=instance), many=True).data
        representation['submitted_user'] = customUserSerializer(instance.form_submission.submitted_user, read_only=True).data

        return representation


class IntakeFormTaskMappingSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form
    """

    class Meta:
        model = FormTaskMapping
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['assign_to'] = customUserSerializer(instance.assign_to, read_only=True).data
        representation['assign_to']['username'] = f"{representation['assign_to']['first_name']}" \
                                                  f" {representation['assign_to']['last_name']}"

        return representation


class FormTaskDetailSerializer(serializers.ModelSerializer):
    form_submission = FormSubmissionsSerializer()

    class Meta:
        model = FormTask
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        form_task_map_data = FormTaskMapping.objects.filter(form_task_id=instance.id)
        representation['user_details'] = IntakeFormTaskMappingSerializer(form_task_map_data, many=True,
                                                                         read_only=True).data
        return representation
