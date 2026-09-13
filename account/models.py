from django.db import models
from organization.models import Organization
from django.contrib.auth.models import AbstractUser

class Accounts(AbstractUser):
	username = models.CharField(max_length=50, unique=True)
	first_name = models.CharField(max_length=50)
	last_name = models.CharField(max_length=50, blank=True)
	org_id = models.ForeignKey(
		Organization,
		on_delete=models.PROTECT,
		blank=True,
		null=True,
	)