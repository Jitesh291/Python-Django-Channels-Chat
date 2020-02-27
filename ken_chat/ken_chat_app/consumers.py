# from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from . import models
from .app_classes.enums import KenanteChatMessageType
from .app_classes.mongo_database import MongoDatabase
# from channels.generic.websocket import WebsocketConsumer
import json
import datetime


class ChatConsumer(AsyncWebsocketConsumer):
    users = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = 'chat_room_%s' % self.room_id
        # Todo: Uncomment this code to switch to mongo db
        #self.db = MongoDatabase()

    async def connect(self):
        # Join room group

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Let User Know they connected
        users_online = []
        for room_id, users in self.users.items():
            if int(room_id) is int(self.room_id):
                for id, channel in users.items():
                    message = {
                        'action': KenanteChatMessageType.ServerNotify.name,
                        'user_id': id,
                        'channel': channel
                    }
                    users_online.append(message)

        if self.room_id not in self.users:
            self.users[self.room_id] = {}
            self.users[self.room_id][self.user_id] = self.channel_name
        else:
            self.users[self.room_id][self.user_id] = self.channel_name

        # self.users[self.user_id] = self.channel_name

        message = {
            'action': KenanteChatMessageType.ServerNotify.name,
            'message': 'connected',
            'user_id': self.user_id,
            'channel': self.channel_name,
            'users_online': users_online
        }

        await self.channel_layer.send(
            self.channel_name,
            {
                'type': 'notify_user_from_server',
                'message': message
            }
        )

        await self.notifyAboutUser("joined")

        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'notify_user_from_server',
        #         'message': message,
        #     }
        # )

    async def notifyAboutUser(self, status):
        for room_id, users in self.users.items():
            if int(room_id) is int(self.room_id):
                for id, channel in users.items():
                    if id is not self.user_id:
                        message = {
                            'action': KenanteChatMessageType.ServerNotify.name,
                            'message': status,
                            'user_id': self.user_id,
                            'channel': self.channel_name
                        }
                        await self.channel_layer.send(
                            channel,
                            {
                                'type': 'notify_user_from_server',
                                'message': message
                            }
                        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.notifyAboutUser("left")
        self.users[self.room_id].pop(self.user_id)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        await self.performAction(text_data_json)

    # Perform action on message received based on action type
    async def performAction(self, message):
        action = message['action']

        if action == KenanteChatMessageType.Leave.name:
            # Close this user's connection
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.notifyAboutUser("left")
            # sender_id = message['sender_id']
            # self.users.pop(sender_id)
        elif action == KenanteChatMessageType.Text.name or action == KenanteChatMessageType.Media.name:
            room_id = message['room_id']
            if int(room_id) is int(self.room_id):
                # Send message to receiver id
                timestamp = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc).timestamp()
                message['timestamp'] = timestamp
                channel = message['channel']
                await self.channel_layer.send(
                    channel,
                    {
                        'type': 'chat_message',
                        'message': message
                    }
                )
                # Send message to room group
                # Todo: Remove this if condition (but not what's inside it) when switching to mongo db
                if action == KenanteChatMessageType.Text.name:
                    await self.save_message(message)

        elif action == KenanteChatMessageType.History.name:
            room_id = message['room_id']
            receiver_id = message['receiver_id']
            channel = self.channel_name
            # Todo: Comment this code when using mongo db
            history = models.ChatMessage.objects.getHistory(room_id, receiver_id)
            # Todo: Uncomment this code to switch to mongo db
            #history = self.db.getHistory(room_id, receiver_id)
            history_message = {
                'action': KenanteChatMessageType.ServerNotify.name,
                'message': 'history',
                'room_id': room_id,
                'user_id': receiver_id,
                'history': history
            }

            await self.channel_layer.send(
                channel,
                {
                    'type': 'notify_user_from_server',
                    'message': history_message
                }
            )

        elif action == KenanteChatMessageType.ServerNotify.name:
            # This will probably not be called here since client will not send server notifications
            # ServerNotify is used only for server to client messages
            pass

    # This is direct communication between two users. (Sender to Receiver)

    async def chat_message(self, event):
        message = event['message']
        # Send message to WebSocket

        await self.send(text_data=json.dumps({
            'message': message
        }))

    # Send an event from server to the client(user)
    async def notify_user_from_server(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def save_message(self, message):
        # Todo: Comment this code when switching to mongo db
        models.ChatMessage.objects.insertMessage(message)
        # Todo: Uncomment this code to switch to mongo db
        # try:
        #     self.db.insertTextMessage(message)
        # except Exception as e:
        #     print(e)

