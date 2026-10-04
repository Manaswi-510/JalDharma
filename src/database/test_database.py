from sqlalchemy import text
from connection import engine


def test_database():
    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT COUNT(*) FROM villages;")
            )

            count = result.fetchone()[0]

            print("Database connection successful!")
            print(f"Number of villages in database: {count}")

    except Exception as e:
        print("Database test failed!")
        print(e)


if __name__ == "__main__":
    test_database()