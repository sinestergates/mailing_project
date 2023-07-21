from django.db import models


class Malling(models.Model):
    day_time_start = models.DateTimeField()
    message_text = models.TextField()
    mobile_code = models.TextField(max_length=32, blank=True)
    tag = models.TextField(blank=True)
    day_time_end = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'Malling'


class Client(models.Model):
    mobile_number = models.IntegerField()
    mobile_code = models.TextField(max_length=32)
    tag = models.TextField()
    timezone = models.CharField(max_length=32, default='GMT+3')

    class Meta:
        managed = True
        db_table = 'Client'


class Message(models.Model):
    day_time_create = models.DateTimeField(auto_now_add=True)
    status = models.TextField()
    malling = models.ForeignKey(Malling, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'Message'
