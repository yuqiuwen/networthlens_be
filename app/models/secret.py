import bcrypt
from app.models.module import *


class UserSecretsModel(BaseModel, TSModel):

    """ 用户密钥箱
    code: 业务码，表示密钥用于指定业务，UserSecretCode
    """

    __tablename__ = "user_secret"

    __table_args__ = (UniqueConstraint("user_id", "code"),)

    id = Column(String(26), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    code = Column(String(20), nullable=False)
    secret_hash = Column(String(128), nullable=False)

    @property
    def password(self):
        raise AttributeError("can't read secret!")

    @password.setter
    def secret(self, value):
        salt = bcrypt.gensalt(rounds=12)
        self.secret_hash = bcrypt.hashpw(value.encode("utf-8"), salt).decode()

    def secret_valid(self, secret):
        """验证密码是否正确"""
        if not self.secret_hash:
            return False

        return bcrypt.checkpw(secret.encode("utf-8"), self.secret_hash.encode("utf8"))