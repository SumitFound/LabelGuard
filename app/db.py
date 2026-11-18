from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from pathlib import Path

DB_PATH=Path(__file__).resolve().parents[1]/'labelguard.sqlite3'
engine=create_engine(f'sqlite:///{DB_PATH}',connect_args={'check_same_thread':False})
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False); Base=declarative_base()
class Scan(Base):
    __tablename__='scans'
    id=Column(Integer,primary_key=True); created_at=Column(DateTime,default=datetime.utcnow,index=True); filename=Column(String); score=Column(Float); verdict=Column(String); result_json=Column(Text); image_url=Column(String)
Base.metadata.create_all(engine)
