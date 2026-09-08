from django.db import models
from django.db.models import ForeignKey
from organization.models import Organization
# Create your models here.


class Events(models.Model):
	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=100, unique=True)
	venue = models.CharField(max_length=50)
	no_of_attendies = models.IntegerField()
	start_time = models.CharField(max_length=8)
	end_time = models.DateField(max_length=8)

	org_id = ForeignKey(
		Organization,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)
