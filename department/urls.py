from django.urls import path

from .views import DepartmentListCreate

urlpatterns = [
	path('department/', DepartmentListCreate.as_view())
]