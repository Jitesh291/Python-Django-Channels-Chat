from django.db import models
from django.db.models import Q


# Create your models here.


class ChatMessageManager(models.Manager):

    def insertMessage(self, message):
        room_id = message['room_id']
        sender = message['sender_id']
        receiver = message['receiver_id']
        msg = message['message']
        action = message['action']
        timestamp = message['timestamp']
        #media_url = message['media_url']

        msgToInsert = self.model(room_id=room_id, sender_id=sender, receiver_id=receiver, message=msg,
                                 action=action, timestamp=timestamp, media_url="")

        try:
            msgToInsert.save(using=self._db)
        except Exception as e:
            print(e)

    def getHistory(self, roomId, receiverId):

        history = list(
            ChatMessage.objects.filter(Q(room_id=roomId), Q(sender_id=receiverId) | Q(receiver_id=receiverId)).values())

        return history


class ChatMessage(models.Model):
    room_id = models.IntegerField()
    sender_id = models.IntegerField()
    receiver_id = models.IntegerField()
    message = models.CharField(max_length=255, default="na")
    action = models.CharField(max_length=100, default="na")
    media_url = models.CharField(max_length=255, default="na")
    timestamp = models.CharField(max_length=255, default="na")

    objects = ChatMessageManager()

    def __str__(self):
        return str(self.room_id)
