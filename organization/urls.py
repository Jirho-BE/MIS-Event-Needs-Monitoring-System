from django.urls import path

from .views import *

urlpatterns = [
	path('organization-create/', OrganizationViewSet.as_view({'post': 'create'})),
    path('organization-delete/<int:pk>/', OrganizationViewSet.as_view({'delete': 'destroy'})),
    path('organization-edit/<int:pk>/', OrganizationViewSet.as_view({'patch': 'partial_update'})),
    path('organization-list/', OrganizationViewSet.as_view({'get': 'list'})),
]