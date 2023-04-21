import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class User(SqlAlchemyBase):
    __tablename__ = 'results'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    test = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    result = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)