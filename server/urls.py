from django.urls import path, include

urlpatterns = [
	path('api/', include('events.urls')),
	path('api/', include('organization.urls')),
	path('api/', include('department.urls')),
	path('api/', include('college.urls')),
    path('api/', include('account.urls')),
    path('api/', include('item.urls')),
    path('api/', include('needs.urls')),
    path('api/', include('event_needs.urls')),
]