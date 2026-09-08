from django.urls import path

from .views import EventNeedsListCreate

urlpatterns = [
	path('event-needs/', EventNeedsListCreate.as_view())
]