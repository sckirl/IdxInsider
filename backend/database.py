import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use the direct IP discovered: 172.19.0.2 for the production openinsider-db container
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@172.19.0.2:5432/openinsider")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
