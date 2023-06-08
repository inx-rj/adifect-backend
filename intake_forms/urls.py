from django.urls import path

from intake_forms.views import IntakeFormRetrieveUpdateDestroyView, IntakeFormListCreateView, \
    IntakeFormFieldListCreateView, IntakeFormFieldRetrieveUpdateDestroyView

urlpatterns = [
    path('', IntakeFormListCreateView.as_view(), name='list_create_intake_forms'),
    path('<int:id>/', IntakeFormRetrieveUpdateDestroyView.as_view(), name='retrieve_update_destroy_intake_forms'),
    path('fields/', IntakeFormFieldListCreateView   .as_view(), name='list_create_intake_form_fields'),
    path('fields/<int:intake_form_id>/<int:version>/', IntakeFormFieldRetrieveUpdateDestroyView.as_view(), name='retrieve_update_destroy_intake_form_fields'),
]
