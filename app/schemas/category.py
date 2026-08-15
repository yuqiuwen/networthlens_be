from pydantic import BaseModel, Field
from app.schemas.common import EntityModel

from app.constant import CategoryType


class CreateCategorySchema(BaseModel):
    category_type: CategoryType
    parent_id: str | None = None
    name: str = Field(max_length=50)
    code: str | None = Field(default=None, max_length=50)
    icon: str | None = None
    color: str | None = None
    sort_no: int = 0


class UpdateCategorySchema(BaseModel):
    parent_id: str | None = None
    name: str | None = Field(default=None, max_length=50)
    code: str | None = Field(default=None, max_length=50)
    icon: str | None = None
    color: str | None = None
    sort_no: int | None = None


class CategorySchema(EntityModel):
    id: str
    category_type: CategoryType
    parent_id: str | None
    name: str
    code: str | None
    icon: str | None
    color: str | None
    sort_no: int
    


class CategoryQuerySchema(BaseModel):
    category_type: CategoryType | None = None
