from sqlalchemy import text
from connection import engine


query = text("""
    INSERT INTO villages (
        village_id,
        village_name,
        latitude,
        longitude,
        population,
        households,
        vulnerability_score,
        priority_score
    )
    VALUES (
        :village_id,
        :village_name,
        :latitude,
        :longitude,
        :population,
        :households,
        :vulnerability_score,
        :priority_score
    )
    ON CONFLICT (village_id) DO NOTHING;
""")


try:
    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "village_id": "TEST001",
                "village_name": "Test Village",
                "latitude": 18.5204,
                "longitude": 73.8567,
                "population": 5000,
                "households": 1000,
                "vulnerability_score": 0.65,
                "priority_score": 0.70
            }
        )

    print("Test village inserted successfully!")

except Exception as e:
    print("Insert failed!")
    print(e)