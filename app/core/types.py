from typing import TypeVar

from sqlalchemy.orm import DeclarativeBase

from app.constant import SysActionEnum, SysAnnounceActionEnum


Model = TypeVar("Model", bound=DeclarativeBase)


TActionEnum =  SysAnnounceActionEnum | SysActionEnum
