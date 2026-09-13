from django.urls import path

from .views import *

urlpatterns = [
	path('department-list/', DepartmentList.as_view()),
    path('department-create/', DepartmentCreate.as_view())
]