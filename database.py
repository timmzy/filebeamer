__author__ = 'Adelola'

from peewee import *
from playhouse.sqlite_ext import SqliteDatabase
import datetime

db = SqliteDatabase("history.db")

filetype = (("M","Media"),
            ("D","Docs"),
            ("F","Files"))

who = ((1,1),(0,0))
class BaseModel(Model):
    class Meta:
        database = db

class History(BaseModel):
    filename = CharField(max_length=100)
    size = CharField(max_length=20)
    time_stamp = DateTimeField()
    type = CharField(choices=filetype)
    sender = IntegerField(choices=who)
    path = CharField(max_length=500)

class Database:
    def createTable(self):
        db.connect()
        db.create_tables([History])

    def deleteTable(self):
        db.connect()
        db.drop_tables([History])
