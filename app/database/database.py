from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import declarative_base, sessionmaker  # type: ignore

# Connect to the Supabase
SQLALCHEMY_DATABASE_URL = (
    "postgresql://postgres.agbkhtpizxahatjawfdy:SoftDev26$$@aws-1-eu-central-2.pooler.supabase.com:6543/postgres"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
