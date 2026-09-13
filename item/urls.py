from django.urls import path

from .views import *

urlpatterns = [
	path('items-list/', ItemList.as_view()),
    path('items-create/', ItemCreate.as_view())
]