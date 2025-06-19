from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime, timedelta

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_email = Column(String, unique=True)
    status = Column(String)  
    subscription_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
