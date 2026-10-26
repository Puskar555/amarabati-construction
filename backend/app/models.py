from typing import Literal
from pydantic import BaseModel, Field, field_validator

class Register(BaseModel):
    name: str = Field(min_length=2,max_length=80)
    email: str = Field(min_length=5,max_length=160)
    password: str = Field(min_length=12,max_length=128)
    region: str = Field(default='',max_length=80)
    @field_validator('email')
    @classmethod
    def normalize_email(cls, v):
        v = v.strip().lower()
        if '@' not in v or ' ' in v: raise ValueError('Invalid email')
        return v

class Login(BaseModel):
    email: str
    password: str
    otp: str | None = None

class Consent(BaseModel):
    analytics: bool = False

class Event(BaseModel):
    type: str
    details: dict = Field(default_factory=dict)
    region: str = Field(default='',max_length=80)
    event_id: str = Field(min_length=12,max_length=80)

class CartLine(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0,le=1000)

class OrderRequest(BaseModel):
    items: list[CartLine] = Field(min_length=1,max_length=40)
    delivery_region: str = Field(min_length=2,max_length=80)
    notes: str = Field(default='',max_length=600)

class Project(BaseModel):
    title: str = Field(min_length=2,max_length=100)
    project_type: Literal['residential','commercial']
    municipality: str = Field(min_length=2,max_length=120)
    width_m: float = Field(ge=3,le=1000)
    depth_m: float = Field(ge=3,le=1000)
    floors: int = Field(ge=1,le=20)
    requirements: dict = Field(default_factory=dict)

class RateProposal(BaseModel):
    product_id: int = Field(gt=0)
    region: str = Field(min_length=2,max_length=80)
    unit_rate: float = Field(gt=0,le=1000000000)
    currency: Literal['NPR'] = 'NPR'
    note: str = Field(min_length=6,max_length=500)

class NewProduct(BaseModel):
    slug: str = Field(pattern=r'^[a-z0-9-]{3,100}$')
    name: str = Field(min_length=3,max_length=160)
    category: str = Field(min_length=2,max_length=100)
    unit: str = Field(min_length=1,max_length=20)
    description: str = Field(default='',max_length=1500)
    specification: str = Field(default='',max_length=300)
