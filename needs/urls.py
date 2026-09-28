from django.urls import path

from .views import *

urlpatterns = [
	path('needs-create/', NeedsViewSet.as_view({'post': 'create'})),
	path('needs-list/', NeedsViewSet.as_view({'get': 'list'})),
	path('needs/<int:pk>/', NeedsViewSet.as_view({'get': 'retrieve'})),
	path('needs/edit/<int:pk>/', NeedsViewSet.as_view({'patch': 'partial_update'})),
	path('needs/delete/<int:pk>/', NeedsViewSet.as_view({'delete': 'destroy'})),
]