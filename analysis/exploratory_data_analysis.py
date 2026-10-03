import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# 1. PROJECT PATHS

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "synthetic"
OUTPUT_DIR = BASE_DIR / "outputs" / "plots"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 2. LOAD DATASETS


village_df = pd.read_csv(DATA_DIR / "1_village_dataset.csv")
demand_df = pd.read_csv(DATA_DIR / "2_historical_water_demand_dataset.csv")
weather_df = pd.read_csv(DATA_DIR / "3_weather_dataset.csv")
source_df = pd.read_csv(DATA_DIR / "4_water_source_dataset.csv")
pipeline_df = pd.read_csv(DATA_DIR / "5_pipeline_water_network_dataset.csv")
tank_df = pd.read_csv(DATA_DIR / "6_tank_reservoir_dataset.csv")
allocation_df = pd.read_csv(DATA_DIR / "7_historical_water_allocation_dataset.csv")
availability_df = pd.read_csv(DATA_DIR / "8_water_availability_dataset.csv")
quality_df = pd.read_csv(DATA_DIR / "9_water_quality_dataset.csv")
gis_pipelines_df = pd.read_csv(DATA_DIR / "10_gis_pipelines.csv")
gis_sources_df = pd.read_csv(DATA_DIR / "10_gis_sources.csv")
gis_tanks_df = pd.read_csv(DATA_DIR / "10_gis_tanks.csv")
gis_villages_df = pd.read_csv(DATA_DIR / "10_gis_villages.csv")
scenario_df = pd.read_csv(DATA_DIR / "11_scenario_simulation_dataset.csv")



# 3. BASIC INFORMATION


print("\n========== DATASET SHAPES ==========")

print("Village:", village_df.shape)
print("Demand:", demand_df.shape)
print("Weather:", weather_df.shape)
print("Source:", source_df.shape)
print("Pipeline:", pipeline_df.shape)
print("Tank:", tank_df.shape)
print("Allocation:", allocation_df.shape)
print("Availability:", availability_df.shape)
print("Quality:", quality_df.shape)
print("Scenario:", scenario_df.shape)



# 4. MISSING VALUE CHECK


print("\n========== MISSING VALUES ==========")

print("\nVillage:")
print(village_df.isnull().sum())

print("\nDemand:")
print(demand_df.isnull().sum())

print("\nWeather:")
print(weather_df.isnull().sum())

print("\nScenario:")
print(scenario_df.isnull().sum())



# 5. DATE CONVERSION


demand_df["date"] = pd.to_datetime(
    demand_df["date"],
    format="%d-%m-%Y"
)

weather_df["date"] = pd.to_datetime(
    weather_df["date"],
    format="%Y-%m-%d"
)


# PLOT 1
# TOTAL WATER DEMAND OVER TIME


daily_demand = (
    demand_df
    .groupby("date")["actual_demand_l"]
    .sum()
    .reset_index()
)

plt.figure(figsize=(14, 6))

plt.plot(
    daily_demand["date"],
    daily_demand["actual_demand_l"]
)

plt.title("Total Water Demand Over Time")
plt.xlabel("Date")
plt.ylabel("Total Actual Water Demand (Litres)")
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "01_total_water_demand.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()



# PLOT 2
# DEMAND WITH 7-DAY AND 30-DAY ROLLING AVERAGES


daily_demand["7_day_avg"] = (
    daily_demand["actual_demand_l"]
    .rolling(window=7)
    .mean()
)

daily_demand["30_day_avg"] = (
    daily_demand["actual_demand_l"]
    .rolling(window=30)
    .mean()
)

plt.figure(figsize=(14, 6))

plt.plot(
    daily_demand["date"],
    daily_demand["actual_demand_l"],
    label="Daily Demand"
)

plt.plot(
    daily_demand["date"],
    daily_demand["7_day_avg"],
    label="7-Day Average"
)

plt.plot(
    daily_demand["date"],
    daily_demand["30_day_avg"],
    label="30-Day Average"
)

plt.title("Water Demand with Rolling Averages")
plt.xlabel("Date")
plt.ylabel("Water Demand (Litres)")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "02_demand_rolling_average.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()



# PLOT 3
# RAINFALL VS TOTAL WATER DEMAND


daily_weather_demand = (
    demand_df
    .groupby("date")
    .agg(
        rainfall_mm=("rainfall_mm", "mean"),
        total_demand_l=("actual_demand_l", "sum")
    )
    .reset_index()
)

plt.figure(figsize=(10, 6))

plt.scatter(
    daily_weather_demand["rainfall_mm"],
    daily_weather_demand["total_demand_l"],
    alpha=0.6
)

plt.title("Rainfall vs Total Water Demand")
plt.xlabel("Average Rainfall (mm)")
plt.ylabel("Total Water Demand (Litres)")
plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "03_rainfall_vs_demand.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()



# PLOT 4
# TEMPERATURE VS TOTAL WATER DEMAND


daily_temp_demand = (
    demand_df
    .groupby("date")
    .agg(
        temperature_c=("temperature_c", "mean"),
        total_demand_l=("actual_demand_l", "sum")
    )
    .reset_index()
)

plt.figure(figsize=(10, 6))

plt.scatter(
    daily_temp_demand["temperature_c"],
    daily_temp_demand["total_demand_l"],
    alpha=0.6
)

plt.title("Temperature vs Total Water Demand")
plt.xlabel("Average Temperature (°C)")
plt.ylabel("Total Water Demand (Litres)")
plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "04_temperature_vs_demand.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()



# PLOT 5
# AVERAGE WATER DEMAND BY VILLAGE


village_demand = (
    demand_df
    .groupby("village_id")["actual_demand_l"]
    .mean()
    .sort_values(ascending=False)
)

plt.figure(figsize=(12, 6))

village_demand.plot(kind="bar")

plt.title("Average Water Demand by Village")
plt.xlabel("Village")
plt.ylabel("Average Water Demand (Litres)")
plt.xticks(rotation=45)
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "05_demand_by_village.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()



# PLOT 6
# AVERAGE WATER DEMAND BY SEASON


date_season = (
    weather_df[["date", "season"]]
    .drop_duplicates()
)

demand_with_season = demand_df.merge(
    date_season,
    on="date",
    how="left"
)

season_demand = (
    demand_with_season
    .groupby("season")["actual_demand_l"]
    .mean()
)

season_order = [
    "Winter",
    "Summer",
    "Monsoon",
    "Post-Monsoon"
]

available_seasons = [
    season
    for season in season_order
    if season in season_demand.index
]

season_demand = season_demand.reindex(
    available_seasons
)

plt.figure(figsize=(8, 5))

season_demand.plot(kind="bar")

plt.title("Average Water Demand by Season")
plt.xlabel("Season")
plt.ylabel("Average Water Demand (Litres)")
plt.xticks(rotation=0)
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "06_demand_by_season.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()



# PLOT 7
# CORRELATION HEATMAP


corr_columns = [
    "population",
    "temperature_c",
    "rainfall_mm",
    "humidity",
    "previous_day_demand_l",
    "demand_7day_avg_l",
    "demand_30day_avg_l",
    "actual_demand_l"
]

correlation = demand_df[corr_columns].corr()

plt.figure(figsize=(10, 7))

sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0
)

plt.title("Correlation Between Water Demand and Prediction Features")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "07_correlation_heatmap.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# COMPLETION MESSAGE

print("EDA COMPLETED SUCCESSFULLY")

print(f"\nPlots saved in:")
print(OUTPUT_DIR)

print("\nGenerated plots:")

print("1. 01_total_water_demand.png")
print("2. 02_demand_rolling_average.png")
print("3. 03_rainfall_vs_demand.png")
print("4. 04_temperature_vs_demand.png")
print("5. 05_demand_by_village.png")
print("6. 06_demand_by_season.png")
print("7. 07_correlation_heatmap.png")