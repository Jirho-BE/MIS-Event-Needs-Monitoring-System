from django.urls import path

from .views import *

urlpatterns = [
	path('login/', AccountLogin.as_view()),
	path('register/', AccountViewSet.as_view({'post': 'create'})),
	path('account-lists/', AccountViewSet.as_view({'get': 'list'})),
    path('profile/<str:username>/', AccountViewSet.as_view({'get': 'retrieve'})),
    path('profile/edit/<str:username>/', AccountViewSet.as_view({'put': 'update'})),
    path('profile/edit-field/<str:username>/', AccountViewSet.as_view({'patch': 'partial_update'})),
    path('profile/delete/<str:username>/', AccountViewSet.as_view({'delete': 'destroy'})),
]