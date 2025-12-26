from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config.config import settings

engine = create_async_engine(settings.db_url)
SessionLocal = async_sessionmaker(engine)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session
