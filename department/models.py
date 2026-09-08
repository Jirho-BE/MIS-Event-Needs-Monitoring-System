from django.db import models
from django.db.models import ForeignKey

from college.models import College


class Department(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50, unique=True)

	college_id = models.ForeignKey(
		College,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)