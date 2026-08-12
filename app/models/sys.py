from app.models.module import *


class SettingsModel(BaseModel, TSModel, BigOperatorModel, StateModel):
    """系统设置"""

    __tablename__ = "settings"

    name = Column(String(100), nullable=False, unique=True, comment="设置唯一名称")
    label = Column(String(50), nullable=False, comment="设置显示名称")
    value = Column(String(255), nullable=False, comment="设置值")
    description = Column(String(100), comment="描述")
    group = Column(String(20), nullable=False, comment="设置分组 SettingsGroup")

