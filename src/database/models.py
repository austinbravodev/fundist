from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Progress(Base):
    __tablename__ = "progress"

    tag = Column(String, primary_key=True)
    currency = Column(String, primary_key=True)
    amount = Column(Float, nullable=False)
    number = Column(Integer, default=1)
