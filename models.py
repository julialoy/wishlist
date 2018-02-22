from datetime import date

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin

from peewee import *

DATABASE = SqliteDatabase('wishlist.db')


class BaseModel(Model):
    class Meta:
        database = DATABASE


class User(UserMixin, BaseModel):
    email = CharField(unique=True)
    password = CharField(max_length=100)
    is_admin = BooleanField(default=False)

    @classmethod
    def create_user(cls, email, password, admin=False):
        try:
            with DATABASE.transaction():
                cls.create(
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=admin,
                )
        except IntegrityError:
            raise ValueError("That email or username is already in use.")

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def is_active(self):
        return self.authenticated

    def is_anonymous(self):
        return False


class Wishlist(BaseModel):
    user = ForeignKeyField(User)
    title = CharField(unique=True, max_length=50)


class Item(BaseModel):
    wishlist = ForeignKeyField(Wishlist)
    name = CharField(unique=True, max_length=100)
    link = CharField()
    date_added = DateField(default=date.today().isoformat())


class UserInfo(BaseModel):
    user = ForeignKeyField(User)
    bio = CharField(max_length=500)
    pic = CharField()


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Wishlist, Item, UserInfo], safe=True)
    DATABASE.close()
