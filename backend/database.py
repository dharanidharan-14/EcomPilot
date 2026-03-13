from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./ecommerce_agent.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class DBReport(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    product_name = Column(String)
    platform = Column(String)
    rating = Column(Float)
    total_reviews = Column(Integer)
    complaint_clusters = Column(JSON)
    listing_mismatches = Column(JSON)
    return_risk_score = Column(Integer)
    risk_level = Column(String)
    top_return_reasons = Column(JSON)
    recommendations = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
