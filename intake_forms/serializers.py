from datetime import datetime

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

    def validate_title(self, value):
        if self.context.get('id'):
            if IntakeForm.objects.exclude(id=self.context.get('id')).filter(title=value, is_trashed=False).exists():
                raise serializers.ValidationError("Title already exists.")
        elif IntakeForm.objects.filter(title=value, is_trashed=False).exists():
            raise serializers.ValidationError("Title already exists.")
        return value


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
            if not fields_data:
                raise ValidationError({"fields": ["This field is required!"]})
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
    field_value = serializers.JSONField(required=True)

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

    def create(self, validated_data):
        validated_data["submission_data"] = validated_data.pop("fields")
        instance = IntakeFormSubmissions.objects.create(**validated_data)
        return instance
