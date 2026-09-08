from django.urls import path

from .views import CollegeListCreate

urlpatterns = [
	path('college/', CollegeListCreate.as_view())
]