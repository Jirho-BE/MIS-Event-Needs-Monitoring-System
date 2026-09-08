from django.urls import path

from .views import NeedssListCreate

urlpatterns = [
	path('needs/', NeedssListCreate.as_view())
]