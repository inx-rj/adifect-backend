import os
import uuid
from datetime import datetime

import boto3
import botocore.exceptions
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from authentication.models import CustomUser
from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormFieldVersion, IntakeFormSubmissions


class IntakeFormSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form
    """

    class Meta:
        model = IntakeForm
        fields = '__all__'


class IntakeFormFieldVersionSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form field
    """
    intake_form = IntakeFormSerializer()

    class Meta:
        model = IntakeFormFieldVersion
        fields = '__all__'


class IntakeFormFieldSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form field serializer
    """
    form_version_data = serializers.SerializerMethodField()
    version = serializers.FloatField(required=False)
    field_name = serializers.CharField(required=False)
    field_type = serializers.CharField(required=False)

    class Meta:
        model = IntakeFormFields
        fields = '__all__'

    def get_form_version_data(self, obj):
        return IntakeFormFieldVersionSerializer(instance=obj.form_version).data

    def create(self, validated_data):
        fields_data = self.context.get("fields", [])
        with transaction.atomic():
            if fields_data:
                form_version_obj = IntakeFormFieldVersion.objects.create(intake_form=self.context.get('intake_form'),
                                                                         version=self.context.get('version'),
                                                                         user=self.context.get('user'))
            for field in fields_data:
                if not field.get('field_name'):
                    raise serializers.ValidationError({"field_name": ["This field is required!"]})
                field_type = field.get('field_type')
                if not field_type:
                    raise serializers.ValidationError({"field_type": ["This field is required!"]})
                if field_type in ['Dropdown', 'Multi-Select Dropdown', 'Radio Button'] and not field.get('options'):
                    raise serializers.ValidationError({"options": ["Please give options!"]})

                field['form_version'] = form_version_obj
                try:
                    IntakeFormFields(**field).full_clean()
                except ValidationError as e:
                    raise serializers.ValidationError(e.message_dict) from e
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
        if data.get("field_type") == 'Short Answer' and len(data.get("field_value")) > 500:
            raise serializers.ValidationError({f"{data.get('field_name')}": "Limit 500 characters"})
        elif data.get("field_type") == 'Date' and not self.is_valid_date(date_string=data.get("field_value")):
            raise serializers.ValidationError({f"{data.get('field_name')}": "Invalid date!"})
        elif data.get("field_type") == 'Date Range' and not self.is_valid_date(
                date_string=data.get("field_value").get("start_date")) and not self.is_valid_date(
            date_string=data.get("field_value").get("end_date")):
            raise serializers.ValidationError({f"{data.get('field_name')}": "Invalid date range!"})

        if data.get("field_type") == "Upload Attachment" and not self.context.get('files').get(data.get("field_value")):
            raise serializers.ValidationError(
                {f"{data.get('field_name')}": "File attachment not found for this field."})
        elif data.get("field_type") == "Upload Attachment" and self.context.get('files').get(data.get("field_value")):
            data["field_value"] = self.context.get('files').get(data.get("field_value"))

        return data


class IntakeFormSubmitSerializer(serializers.ModelSerializer):
    form_version = serializers.PrimaryKeyRelatedField(required=True,
                                                      queryset=IntakeFormFieldVersion.objects.filter(is_trashed=False))
    submitted_user = serializers.PrimaryKeyRelatedField(required=True,
                                                        queryset=CustomUser.objects.filter(is_trashed=False))
    fields = IntakeFormFieldsSubmitSerializer(many=True, required=True, write_only=True)
    submission_data = serializers.JSONField(read_only=True)

    class Meta:
        model = IntakeFormSubmissions
        fields = ['form_version', 'submitted_user', 'fields', 'submission_data']

    def validate(self, attrs):
        form_field_set = set(IntakeFormFields.objects.filter(form_version=attrs.get("form_version")
                                                             ).values_list('field_name', flat=True))
        submit_form_field_set = set()
        for field in attrs.get("fields"):
            if not IntakeFormFields.objects.filter(form_version=attrs.get("form_version"),
                                                   field_name=field.get("field_name"),
                                                   field_type=field.get("field_type")).exists():
                raise serializers.ValidationError(
                    {"field": f"Invalid field with field_name => {field.get('field_name')}"
                              f" or field_type => {field.get('field_type')}"})

            submit_form_field_set.add(field.get("field_name"))

        if form_field_set - submit_form_field_set:
            for field in form_field_set - submit_form_field_set:
                raise serializers.ValidationError({f"{field}": "This field is required."})

        return attrs

    @staticmethod
    def upload_file_s3(file_obj):
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
            )
            uid = uuid.uuid4()
            file_etx = file_obj.name.split('.')[-1]
            s3_client.upload_fileobj(file_obj,
                                     os.environ.get('AWS_STORAGE_BUCKET_NAME'),
                                     f'intake_form_attachments/{uid}.{file_etx}')

            return f'intake_form_attachments/{uid}.{file_etx}'

        except botocore.exceptions.ClientError as err:
            print(f"## Error {err}")
            return ""

    def create(self, validated_data):
        for field in validated_data.get("fields"):
            if field.get('field_type') == "Upload Attachment":
                field['field_value'] = self.upload_file_s3(file_obj=field.get('field_value'))
        validated_data["submission_data"] = validated_data.pop("fields")
        return IntakeFormSubmissions.objects.create(**validated_data)
