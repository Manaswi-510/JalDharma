from sqlalchemy import text
from connection import engine


query = text("""
    DELETE FROM villages
    WHERE village_id = :village_id;
""")


try:
    with engine.begin() as connection:

        result = connection.execute(
            query,
            {
                "village_id": "TEST001"
            }
        )

        print(f"Rows deleted: {result.rowcount}")

except Exception as e:
    print("Delete failed!")
    print(e)