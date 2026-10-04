import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)


def get_engine():
    """Return a SQLAlchemy engine connected to PostgreSQL."""
    return create_engine(DATABASE_URL)


# Keep module-level engine for existing project files
engine = get_engine()


def test_connection():
    """Test the PostgreSQL database connection."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            print("PostgreSQL connected successfully!")
            print(result.fetchone()[0])
            return True

    except Exception as e:
        print("Database connection failed!")
        print(e)
        return False


if __name__ == "__main__":
    test_connection()