from django.db import models
from django.db.models import ForeignKey

from item.models import Item


class Needs(models.Model):
	id = models.AutoField(primary_key=True)
	quantity = models.IntegerField()
	item_id = models.ForeignKey(
		Item,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)