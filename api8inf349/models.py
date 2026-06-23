import os

from peewee import (
    PostgresqlDatabase, Model, IntegerField, CharField, TextField,
    FloatField, BooleanField, AutoField, ForeignKeyField,
)

DATABASE = PostgresqlDatabase(
    os.environ.get("DB_NAME", "api8inf349"),
    user=os.environ.get("DB_USER", "user"),
    password=os.environ.get("DB_PASSWORD", "pass"),
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", 5432)),
)


class BaseModel(Model):
    class Meta:
        database = DATABASE


class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = FloatField()
    in_stock = BooleanField()
    weight = IntegerField()
    image = CharField()



class ShippingInformation(BaseModel):
    country = CharField()
    address = CharField()
    postal_code = CharField()
    city = CharField()
    province = CharField()


class CreditCard(BaseModel):
    name = CharField()
    first_digits = CharField()
    last_digits = CharField()
    expiration_year = IntegerField()
    expiration_month = IntegerField()


class Transaction(BaseModel):
    id = CharField(primary_key=True)  
    success = BooleanField()
    amount_charged = IntegerField(null=True)
    error_code = CharField(null=True)
    error_name = CharField(null=True)


class Order(BaseModel):
    id = AutoField()
    email = CharField(null=True)
    paid = BooleanField(default=False)
    total_price = FloatField(default=0)
    shipping_price = FloatField(default=0)
    shipping_information = ForeignKeyField(ShippingInformation, null=True)
    credit_card = ForeignKeyField(CreditCard, null=True)
    transaction = ForeignKeyField(Transaction, null=True)
    payment_in_progress = BooleanField(default=False)

class OrderProduct(BaseModel):
    order = ForeignKeyField(Order, backref="items")
    product = ForeignKeyField(Product)
    quantity = IntegerField()

ALL_MODELS = [Product, ShippingInformation, CreditCard, Transaction, Order, OrderProduct]
