from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from intake_forms.models import IntakeForm, IntakeFormFields, IntakeFormFieldVersion


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