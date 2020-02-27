import pymongo
from pymongo import MongoClient

# mongo db version - v4.2.3

connection_url = "mongodb://localhost:27017/"
databaseName = "Kenante"
collectionName = "ChatCollection"


class MongoDatabase:
    collection = None

    def __init__(self):
        # Create mango db client
        self.client = MongoClient(connection_url)
        self.db = self.client[databaseName]

    def createCollectionIfNotExists(self):
        if collectionName in self.db.list_collection_names():
            pass
        else:
            self.db.create_collection(collectionName)
        if self.collection is None:
            self.collection = self.db[collectionName]

    def insertTextMessage(self, message):
        self.createCollectionIfNotExists()
        if self.collection is not None:
            try:
                self.collection.insert_one(message)
            except Exception as e:
                print(e)
        else:
            raise Exception("ERROR!!!\nCollection could not be initialized.\nMessage not stored.")

    def getHistory(self, room_id, user_id):
        history = []
        self.createCollectionIfNotExists()
        if self.collection is not None:
            try:
                query = {"room_id": room_id, "$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}

                record = self.collection.find(query)
                for each in record:
                    if '_id' in each:
                        del each['_id']
                    history.append(each)
            except Exception as e:
                print(e)
        return history
