"""Pydantic 请求/响应模型"""
from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


class CartAddRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class CartUpdateRequest(BaseModel):
    quantity: int = Field(ge=1, le=99)


class ProductCreateRequest(BaseModel):
    category_id: int
    name: str
    description: str = ""
    price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)
    image: str = ""


class ProductUpdateRequest(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    image: Optional[str] = None


class StockUpdateRequest(BaseModel):
    stock: int = Field(ge=0)


class StatusUpdateRequest(BaseModel):
    status: str  # on / off


class PaymentRequest(BaseModel):
    order_id: int
    pay_type: str = "mock"
