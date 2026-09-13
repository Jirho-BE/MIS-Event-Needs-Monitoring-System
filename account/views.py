from django.contrib.auth import authenticate
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from account.permissions import IsAdmin, IsOwnerOrAdmin
from account.models import Accounts
from account.serializers import AccountSerializer


class AccountLogin(APIView):
	permission_classes = [AllowAny]

	def post(self, request):
		username = request.data.get('username')
		password = request.data.get('password')

		if not username or not password:
			return Response(
				data={'message': 'Username and password are required.'},
				status=status.HTTP_400_BAD_REQUEST)
		account = authenticate(username=username, password=password)
		if account is None:
			return Response(
				data={'message': 'Username or password is invalid.'},
				status=status.HTTP_401_UNAUTHORIZED
			)
		refresh = RefreshToken.for_user(account)
		serializer = AccountSerializer(account)
		return Response(
			data={
				'message': 'Login successful',
				'account': serializer.data,
				'tokens': {
					'refresh': str(refresh),
					'access': str(refresh.access_token)
				}
			},
			status=status.HTTP_200_OK
		)


class AccountViewSet(viewsets.ModelViewSet):
	queryset = Accounts.objects.all()
	serializer_class = AccountSerializer
	lookup_field = 'username'
	def get_permissions(self):
		if self.action == 'create':
			permission_classes = [AllowAny]
		elif self.action in ['list', 'destroy']:
			permission_classes = [IsAdmin]
		elif self.action in ['retrieve', 'update', 'partial_update']:
			permission_classes = [IsOwnerOrAdmin]
		else:
			permission_classes = [IsAuthenticated]

		return [permission() for permission in permission_classes]
