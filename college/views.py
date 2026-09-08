from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import College
from .serializers import CollegeSerializer


class CollegeListCreate(APIView):
	def get(self, request):
		roles = College.objects.all()
		serializer = CollegeSerializer(roles, many=True)
		return Response(serializer.data)

	def post(self, request):
		serializer = CollegeSerializer(data=request.data)	
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(
			data=serializer.errors,
			status=status.HTTP_400_BAD_REQUEST
		)