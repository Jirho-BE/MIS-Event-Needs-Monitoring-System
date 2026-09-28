from django.db import models
from django.db.models import ForeignKey

from needs.models import Needs
from events.models import Events
from account.models import Accounts


class EventNeeds(models.Model):
	id = models.AutoField(primary_key=True)
	needs_id = ForeignKey(
		Needs,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)

	event_id = models.ForeignKey(
		Events,
		on_delete=models.SET_NULL,
		null=True,
		blank=True
	)

	owner = models.ForeignKey(
		Accounts,
		on_delete=models.SET(1),
	)