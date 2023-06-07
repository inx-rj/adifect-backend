from django.db import transaction
from rest_framework import serializers

from intake_forms.models import IntakeForm, IntakeFormFields


class IntakeFormSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form
    """

    class Meta:
        model = IntakeForm
        fields = '__all__'

class IntakeFormFieldSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, add and update intake form field serializer
    """
    intake_form = serializers.PrimaryKeyRelatedField(queryset=IntakeForm.objects.filter(is_trashed=False), required=True)
    version = serializers.FloatField(required=False)
    field_name = serializers.CharField(required=False)
    field_type = serializers.CharField(required=False)

    class Meta:
        model = IntakeFormFields
        fields = '__all__'

    def create(self, validated_data):
        fields_data = self.context.get("fields", [])
        with transaction.atomic():
            for field in fields_data:
                if not field.get('field_name'):
                    raise serializers.ValidationError({"field_name": ["This field is required!"]})
                if not field.get('field_type'):
                    raise serializers.ValidationError({"field_type": ["This field is required!"]})
                field['version'] = validated_data.get('version')
                field['intake_form'] = validated_data.get('intake_form')
                IntakeFormFields.objects.create(**field)
        return True