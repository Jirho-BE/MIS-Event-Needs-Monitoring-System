from django.urls import path, include
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
	path('api/', include('events.urls')),
	path('api/', include('organization.urls')),
	path('api/', include('department.urls')),
	path('api/', include('college.urls')),
    path('api/', include('account.urls')),
    path('api/', include('item.urls')),
    path('api/', include('needs.urls')),
    path('api/', include('event_needs.urls')),
    path('', TemplateView.as_view(template_name='index.html')),
]


