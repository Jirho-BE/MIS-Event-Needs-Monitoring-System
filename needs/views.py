from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from account.permissions import IsAdmin, IsOwnerOrAdmin
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Needs
from .serializers import NeedsSerializer


class NeedsViewSet(viewsets.ModelViewSet):
	queryset = Needs.objects.all()
	serializer_class = NeedsSerializer
	def get_permissions(self):
		if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
			permission_classes = [IsOwnerOrAdmin]
		else:
			permission_classes = [IsAuthenticated]
		return [permission() for permission in permission_classes]
	
	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)