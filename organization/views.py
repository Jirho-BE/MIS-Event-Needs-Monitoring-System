from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from account.permissions import IsAdmin, IsOwnerOrAdmin
from .models import Organization
from .serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
	queryset = Organization.objects.all()
	serializer_class = OrganizationSerializer
	def get_permissions(self):
		if self.action == 'create':
			permission_classes = [IsAdmin]
		elif self.action in ['list']:
			permission_classes = [AllowAny]
		elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
			permission_classes = [IsAdmin]
		else:
			permission_classes = [IsAdmin]
		return [permission() for permission in permission_classes]