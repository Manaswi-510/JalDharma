from sqlalchemy import text
from connection import engine


query = text("""
    UPDATE villages
    SET population = :population
    WHERE village_id = :village_id;
""")


try:
    with engine.begin() as connection:

        result = connection.execute(
            query,
            {
                "population": 5500,
                "village_id": "TEST001"
            }
        )

        print(f"Rows updated: {result.rowcount}")

except Exception as e:
    print("Update failed!")
    print(e)