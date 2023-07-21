from rest_framework import serializers

from mailing import models


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Client
        fields = '__all__'


class MallingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Malling
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Message
        fields = '__all__'
