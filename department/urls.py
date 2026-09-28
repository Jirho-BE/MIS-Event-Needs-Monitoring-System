from django.urls import path

from .views import *

urlpatterns = [
	path('department-create/', DepartmentViewSet.as_view({'post': 'create'})),
    path('department-delete/<int:pk>/', DepartmentViewSet.as_view({'delete': 'destroy'})),
    path('department-edit/<int:pk>/', DepartmentViewSet.as_view({'patch': 'partial_update'})),
    path('department-list/', DepartmentViewSet.as_view({'get': 'list'})),
]