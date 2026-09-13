from django.urls import path

from .views import *

urlpatterns = [
	path('organization-list/', OrganizationList.as_view()),
    path('organization-create/', OrganizationCreate.as_view())
]