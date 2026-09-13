from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from account.permissions import IsAdmin, IsOwnerOrAdmin
from .models import Item
from .serializers import ItemSerializer


class ItemList(APIView):
	permission_classes = [AllowAny]
	def get(self, request):
		roles = Item.objects.all()
		serializer = ItemSerializer(roles, many=True)
		return Response(serializer.data)

class ItemCreate(APIView):
	permission_classes = [IsAdmin]
	def post(self, request):
		serializer = ItemSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(
			data=serializer.errors,
			status=status.HTTP_400_BAD_REQUEST
		)