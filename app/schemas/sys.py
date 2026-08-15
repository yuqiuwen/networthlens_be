from typing import Literal

import re

from pydantic import BaseModel, Field, model_validator

from app.ext.crypt import pwd_crypto


class QSecretSchema(BaseModel):
    biz: Literal["user_pwd"]


class SecretCodeSchema(BaseModel):
    code: str = Field(pattern=r"^\d{6}$", description="6位数字查看密钥")


class EncryptedSecretCodeSchema(BaseModel):
    code: str = Field(description="RSA 加密的 6 位数字查看密钥")

    @model_validator(mode="after")
    def decrypt_code(self):
        self.code = pwd_crypto.decrypt(self.code, as_str=True)
        if not re.fullmatch(r"\d{6}", self.code):
            raise ValueError("6位数字查看密钥")
        return self


class SecretStatusSchema(BaseModel):
    configured: bool
