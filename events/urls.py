from django.urls import path

from .views import *

urlpatterns = [
	path('events-create/', EventsViewSet.as_view({'post': 'create'})),
	path('events-list/', EventsViewSet.as_view({'get': 'list'})),
	path('events/<int:pk>/', EventsViewSet.as_view({'get': 'retrieve'})),
	path('events/edit/<int:pk>/', EventsViewSet.as_view({'patch': 'partial_update'})),
	path('events/delete/<int:pk>/', EventsViewSet.as_view({'delete': 'destroy'})),
]