from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Needs
from .serializers import NeedsSerializer


class NeedssListCreate(APIView):
	def get(self, request):
		roles = Needs.objects.all()
		serializer = NeedsSerializer(roles, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = NeedsSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(
			data=serializer.errors,
			status=status.HTTP_400_BAD_REQUEST
		)