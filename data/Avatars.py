import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Avatar(SqlAlchemyBase):
    __tablename__ = 'avatar'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    filename = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
