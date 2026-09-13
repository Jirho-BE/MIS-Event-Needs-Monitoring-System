from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from account.permissions import IsAdmin, IsOwnerOrAdmin
from .models import Organization
from .serializers import OrganizationSerializer


class OrganizationList(APIView):
	permission_classes = [AllowAny]
	def get(self, request):
		roles = Organization.objects.all()
		serializer = OrganizationSerializer(roles, many=True)
		return Response(serializer.data)

class OrganizationCreate(APIView):
	permission_classes = [IsAdmin]
	def post(self, request):
		serializer = OrganizationSerializer(data=request.data)	
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(
			data=serializer.errors,
			status=status.HTTP_400_BAD_REQUEST
		)