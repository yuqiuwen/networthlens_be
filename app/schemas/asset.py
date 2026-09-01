from datetime import date

from pydantic import BaseModel

from app.schemas.category import CategorySchema
from app.schemas.common import EntityModel
from app.constant import (
    AssetStatus,
    AssetType,
    AssetValuationMethod,
    AssetValuationSource,
)


class CreateAssetSchema(BaseModel):
    asset_type: AssetType
    name: str
    category_id: str

    quantity: float = 0
    unit: str | None = None

    purchase_amount: int = 0
    current_value: int = 0

    unit_price: float | None = None

    currency: str = "CNY"
    purchase_date: date | None = None

    valuation_method: AssetValuationMethod = AssetValuationMethod.MANUAL

    image_urls: list[str] = []
    extra_info: dict | None = None

    note: str | None = None


class UpdateAssetSchema(BaseModel):
    name: str | None = None
    quantity: float | None = None
    category_id: str | None = None
    purchase_amount: int | None = None
    current_value: int | None = None
    valuation_method: AssetValuationMethod | None = None
    status: AssetStatus | None = None
    note: str | None = None


class AssetQuerySchema(BaseModel):
    page: int = 1
    limit: int = 20

    asset_type: AssetType | None = None
    category_ids: str | None = None
    status: AssetStatus | None = None


class AssetListSchema(EntityModel):
    id: str
    asset_type: AssetType
    category_id: str | None = None
    category: CategorySchema | None = None
    name: str
    current_value: int
    currency: str
    status: AssetStatus


class AssetDetailSchema(EntityModel):
    id: str
    asset_type: AssetType
    name: str
    category_id: str | None = None

    quantity: float
    unit: str | None

    purchase_amount: int
    current_value: int

    unit_price: float | None

    currency: str
    purchase_date: date | None

    valuation_method: AssetValuationMethod
    status: AssetStatus

    image_urls: list[str]
    extra_info: dict | None

    note: str | None


class CreateAssetValuationSchema(BaseModel):
    valuation: int
    valuation_date: date
    source: AssetValuationSource
    note: str | None = None


class AssetValuationSchema(BaseModel):
    id: str
    valuation: int
    valuation_date: date
    source: AssetValuationSource