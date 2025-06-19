from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubscriptionSchema(BaseModel):
    user_email: str = Field(..., description="The email of the user")
    status: Optional[str] = Field(None, description="Subscription status: active, canceled, etc.")
    subscription_date: Optional[datetime] = Field(None, description="Date when subscription started")
    expiry_date: Optional[datetime] = Field(None, description="Date when subscription expires")
