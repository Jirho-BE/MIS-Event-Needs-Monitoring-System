from django.urls import path

from .views import *

urlpatterns = [
	path('item-create/', ItemViewSet.as_view({'post': 'create'})),
        path('item-delete/<int:pk>/', ItemViewSet.as_view({'delete': 'destroy'})),
        path('item-edit/<int:pk>/', ItemViewSet.as_view({'put': 'update'})),
        path('item-list/', ItemViewSet.as_view({'get': 'list'})),
]