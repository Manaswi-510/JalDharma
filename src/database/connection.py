import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Load environment variables if python-dotenv is available
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "jal_dharma")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_engine():
    """Returns a SQLAlchemy engine connected to the PostgreSQL database."""
    return create_engine(DATABASE_URL)

def test_connection():
    """Tests the connection to the PostgreSQL database."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
            print("Connected successfully to PostgreSQL:")
            print(result)
            return True
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    test_connection()
