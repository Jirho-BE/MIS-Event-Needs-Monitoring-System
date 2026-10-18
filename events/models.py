from django.db import models
from django.db.models import ForeignKey
from organization.models import Organization
from account.models import Accounts


class Events(models.Model):
	id = models.AutoField(primary_key=True)
	date = models.DateField()
	title = models.CharField(max_length=100, unique=True)
	venue = models.CharField(max_length=50)
	no_of_attendies = models.IntegerField()
	start_time = models.CharField(max_length=8)
	end_time = models.CharField(max_length=8)
	approved = models.BooleanField(default=False)
	org_id = ForeignKey(
		Organization,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)

	owner = models.ForeignKey(
		Accounts,
		on_delete=models.SET(1),
	)
