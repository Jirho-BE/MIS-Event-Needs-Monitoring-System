from django.urls import path

from .views import OrganizationListCreate

urlpatterns = [
	path('organization/', OrganizationListCreate.as_view())
]