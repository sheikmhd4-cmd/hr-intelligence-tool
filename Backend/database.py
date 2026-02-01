from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String, default="user")


class CandidateResult(Base):
    __tablename__ = "candidate_results"

    id = Column(Integer, primary_key=True)
    jd_title = Column(String)
    candidate_name = Column(String)

    technical = Column(Float)
    problem_solving = Column(Float)
    system_design = Column(Float)
    communication = Column(Float)

    total_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
