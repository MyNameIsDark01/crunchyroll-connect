import json
import os
import uuid

from uuid import UUID
from datetime import datetime, timedelta


class User:
    # Note the use of var : type is only for debugging and readability. Python is not statically typed so data type can
    # be changed on a whim through assignment
    def __init__(
        self,
        user_id: int,
        etp_guid: str,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        premium: str,
        access_type: str,
        created: str,
        expires: str,
        is_publisher: bool = False
    ):

        self._class = 'user'
        self.user_id = user_id
        self.etp_guid = etp_guid
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.premium = premium
        self.access_type = access_type
        self.created = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S%z")
        self.expires = expires
        self.is_publisher = is_publisher


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return obj.hex
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, User):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

class Config:

    def __init__(self, path: str):
        self.path = path
        self.store = None

    def init_store(self):
        if os.path.isfile(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                self.store = json.loads(f.read())

        else:
            store = dict()
            store['session_id'] = ""
            store['device_id'] = uuid.uuid1()
            store['account'] = ""
            store['password'] = ""
            store['user'] = None
            store['auth'] = ""
            store['user_id'] = ""
            store['cr_locales'] = None

            self.store = store
            self.save()

    def clear_store(self):
        if not self.store: self.init_store()

        self.store['account'] = ""
        self.store['password'] = ""
        self.store['user'] = None
        self.store['auth'] = ""
        self.store['user_id'] = ""
        self.store['cr_locales'] = None
        self.save

    def is_logged_in(self):
        return self.store['account'] != "" and self.store['password'] != ""

    def save(self):
        with open(self.path, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(self.store, cls=JSONEncoder, indent=4))
