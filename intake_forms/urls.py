from django.urls import path

from intake_forms.views import IntakeFormRetrieveUpdateDestroyView, IntakeFormListCreateView, \
    IntakeFormFieldListCreateView, IntakeFormSubmit, IntakeFormFieldRetrieveUpdateDeleteView, ListIntakeFormSubmissions

urlpatterns = [
    path('', IntakeFormListCreateView.as_view(), name='list_create_intake_forms'),
    path('fields/', IntakeFormFieldListCreateView.as_view(), name='list_create_intake_form_fields'),
    path('fields/<str:slug>/', IntakeFormFieldRetrieveUpdateDeleteView.as_view(), name='update_intake_form_fields'),
    path('submit/<str:slug>/', IntakeFormSubmit.as_view(), name='intake_form_submit'),
    path('submit/<int:id>/', IntakeFormSubmit.as_view(), name='get_intake_form_submit'),
    path('responses/<str:slug>/', ListIntakeFormSubmissions.as_view(),
         name='list_intake_form_responses'),
    path('<str:form_slug>/', IntakeFormRetrieveUpdateDestroyView.as_view(),
         name='retrieve_update_destroy_intake_forms'),
]
