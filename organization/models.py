from django.db import models
from django.db.models import ForeignKey

from department.models import Department
from college.models import College


class Organization(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=50, unique=True)

	dept_id = ForeignKey(
		Department,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)

	college_id = models.ForeignKey(
		College,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)