
# volcalc/db.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/volsurface")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    spot = Column(Float)
    r = Column(Float)
    q = Column(Float)
    meta = Column(JSON)

class OptionPoint(Base):
    __tablename__ = "option_points"
    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"))
    strike = Column(Float)
    expiration = Column(DateTime)
    mid = Column(Float)
    iv = Column(Float)
    data = Column(JSON)
    snapshot = relationship("Snapshot", backref="points")

def init_db():
    Base.metadata.create_all(bind=engine)
