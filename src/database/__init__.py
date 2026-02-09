from os import environ

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


try:
    engine = create_async_engine(
        environ["DATABASE_URL"].replace("postgres:", "postgresql+asyncpg:")
    )
except ModuleNotFoundError:
    from sqlalchemy import create_engine

    engine = create_engine(environ["DATABASE_URL"].replace("postgres:", "postgresql:"))
    Session = sessionmaker(engine)
else:
    Session = sessionmaker(engine, class_=AsyncSession)
