from datetime import datetime

from pbkdf2 import crypt
from sqlalchemy import Column, DateTime, Integer, String

from settings import BASE


class Users(BASE):
    """用户注册信息"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), nullable=False, unique=True)  # 不允许为空且唯一
    _password = Column("password", String(100))
    createtime = Column(DateTime, default=datetime.now)
    winnums = Column(Integer, default=0)  # 赢的总次数
    gender = Column(String(3), nullable=False)

    def _hash_password(self, password):
        return crypt(password, iterations=0x2537)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = self._hash_password(password)

    def auth_password(self, pwd):
        if self._password:
            return self.password == crypt(pwd, self.password)
        else:
            return False


class UserGolds(BASE):
    """蝌蚪每局吃的金币数排名"""
    __tablename__ = "user_golds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    rooms = Column(Integer, nullable=False)  # 房间号
    golds = Column(Integer)  # 吃的金币数
    sank = Column(Integer, default=0)  # 排名，默认不排名
    createtime = Column(DateTime, default=datetime.now)
    server = Column(String(30))  # 所在的服务器
