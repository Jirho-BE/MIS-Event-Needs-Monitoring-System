from django.urls import path

from .views import *

urlpatterns = [
	path('event-needs-create/', EventNeedsViewSet.as_view({'post': 'create'})),
	path('event-needs-list/', EventNeedsViewSet.as_view({'get': 'list'})),
	path('event-needs/<int:pk>/', EventNeedsViewSet.as_view({'get': 'retrieve'})),
	path('event-needs/edit/<int:pk>/', EventNeedsViewSet.as_view({'patch': 'partial_update'})),
	path('event-needs/delete/<int:pk>/', EventNeedsViewSet.as_view({'delete': 'destroy'})),
]