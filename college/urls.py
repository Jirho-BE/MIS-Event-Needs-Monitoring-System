from django.urls import path

from .views import *

urlpatterns = [
	path('college-create/', CollegeViewSet.as_view({'post': 'create'})),
    path('college-delete/<int:pk>/', CollegeViewSet.as_view({'delete': 'destroy'})),
    path('college-edit/<int:pk>/', CollegeViewSet.as_view({'put': 'update'})),
    path('college-list/', CollegeViewSet.as_view({'get': 'list'})),
]