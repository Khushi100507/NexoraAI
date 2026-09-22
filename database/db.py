from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH=Path(__file__).resolve().parent/"nexoraa.db"
engine=create_engine(f"sqlite:///{DB_PATH}",connect_args={"check_same_thread":False})
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
Base=declarative_base()

class Operation(Base):
    __tablename__="operations"
    id=Column(Integer,primary_key=True)
    action=Column(String,nullable=False)
    domain=Column(String,nullable=False)
    title=Column(String,nullable=False)
    reason=Column(Text,nullable=False)
    payload=Column(Text,nullable=False)
    risk=Column(String,nullable=False)
    status=Column(String,nullable=False,default="pending_approval")
    created_at=Column(DateTime,default=datetime.utcnow)
    completed_at=Column(DateTime,nullable=True)
    verification=Column(Text,nullable=True)

Base.metadata.create_all(engine)
