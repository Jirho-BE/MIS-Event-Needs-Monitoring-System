from rest_framework import serializers

from .models import EventNeeds


class EventNeedsSerializer(serializers.ModelSerializer):
	class Meta:
		model = EventNeeds
		fields = '__all__'
		read_only_fields = ['owner']