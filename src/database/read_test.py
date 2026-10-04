from sqlalchemy import text
from connection import engine


query = text("""
    SELECT
        village_id,
        village_name,
        latitude,
        longitude,
        population,
        households,
        vulnerability_score,
        priority_score
    FROM villages
    ORDER BY village_id;
""")


try:
    with engine.connect() as connection:

        result = connection.execute(query)

        rows = result.fetchall()

        print("\nVillages in PostgreSQL:")
        print("-" * 80)

        for row in rows:
            print(
                f"ID: {row.village_id} | "
                f"Name: {row.village_name} | "
                f"Population: {row.population} | "
                f"Households: {row.households}"
            )

except Exception as e:
    print("Read failed!")
    print(e)