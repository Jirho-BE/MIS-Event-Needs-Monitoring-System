from django.urls import path

from .views import *

urlpatterns = [
	path('college-create/', CollegeCreate.as_view()),
    path('college-list/', CollegeList.as_view())
]