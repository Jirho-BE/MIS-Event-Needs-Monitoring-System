from django.urls import path

from .views import EventsListCreate

urlpatterns = [
	path('events/', EventsListCreate.as_view())
]