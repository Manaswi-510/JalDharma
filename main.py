import pandas as pd

# Load dataset
df = pd.read_csv('data/synthetic/2_historical_water_demand_dataset.csv')

# Convert date to datetime
df["date"] = pd.to_datetime(df["date"], dayfirst=True)

# Sort by village and date
df = df.sort_values(["village_id", "date"])

# Check dataset structure
print(df.head())
print(df.dtypes)

# Check time-series structure
print("Start date:", df["date"].min())
print("End date:", df["date"].max())
print("Total records:", len(df))
print("Number of villages:", df["village_id"].nunique())

# Features and target
features = [
    "population",
    "temperature_c",
    "rainfall_mm",
    "humidity",
    "previous_day_demand_l",
    "demand_7day_avg_l",
    "demand_30day_avg_l"
]

target = "actual_demand_l"

X = df[features]
y = df[target]

print("Features:")
print(X.head())

print("\nTarget:")
print(y.head())

# ==============================
# TIME-BASED TRAIN/TEST SPLIT
# ==============================
# here basically we are using the first 2 months of data for training and the last month for testing. 
# This is a common approach in time series forecasting to ensure that the model is trained on past data.
# Training data: April + May
# Testing data: June

train_df = df[df["date"] < "2025-06-01"]
test_df = df[df["date"] >= "2025-06-01"]

# Separate features and target
X_train = train_df[features]
y_train = train_df[target]

X_test = test_df[features]
y_test = test_df[target]

print("\nTraining data:")
print("Records:", len(train_df))
print("Start:", train_df["date"].min())
print("End:", train_df["date"].max())

print("\nTesting data:")
print("Records:", len(test_df))
print("Start:", test_df["date"].min())
print("End:", test_df["date"].max())

print("\nX_train shape:", X_train.shape)
print("X_test shape:", X_test.shape)

# ==============================
# FEATURE SCALING
# ==============================

# Calculate mean and standard deviation from training data
train_mean = X_train.mean()
train_std = X_train.std()

# Scale training data
X_train_scaled = (X_train - train_mean) / train_std

# Scale test data using training statistics
X_test_scaled = (X_test - train_mean) / train_std

print("\nScaled training data:")
print(X_train_scaled.head())

print("\nScaled testing data:")
print(X_test_scaled.head())

print("\nScaled training data:")
print(X_train_scaled[:5])

print("\nScaled testing data:")
print(X_test_scaled[:5])

# ==============================
# BUILD NEURAL NETWORK MODEL
# ==============================

import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense

model = Sequential([
    Dense(64, activation="relu", input_shape=(7,)),
    Dense(32, activation="relu"),
    Dense(16, activation="relu"),
    Dense(1)
])

model.compile(
    optimizer="adam",
    loss="mse",
    metrics=["mae"]
)

print("\nModel architecture:")
model.summary()

# ==============================
# TRAIN THE MODEL
# ==============================

history = model.fit(
    X_train_scaled,
    y_train,
    epochs=50,
    batch_size=32,
    validation_split=0.1,
    verbose=1
)

# ==============================
# PREDICT ON TEST DATA
# ==============================

predictions = model.predict(X_test_scaled)

# Convert predictions from 2D array to 1D
predictions = predictions.flatten()

print("\nFirst 10 predictions:")
print(predictions[:10])

print("\nFirst 10 actual values:")
print(y_test.values[:10])

# ==============================
# MODEL EVALUATION
# ==============================

import numpy as np

# Calculate errors
errors = predictions - y_test.values

# Mean Absolute Error
mae = np.mean(np.abs(errors))

# Root Mean Squared Error
rmse = np.sqrt(np.mean(errors ** 2))

# Mean Absolute Percentage Error
mape = np.mean(
    np.abs(errors / y_test.values)
) * 100

print("\n==============================")
print("MODEL PERFORMANCE ON JUNE DATA")
print("==============================")

print(f"MAE:  {mae:,.2f} litres")
print(f"RMSE: {rmse:,.2f} litres")
print(f"MAPE: {mape:.2f}%")

# ==============================
# CHECK TRAINING VS TEST FEATURES
# ==============================

print("\nTraining feature means:")
print(X_train.mean())

print("\nTesting feature means:")
print(X_test.mean())

# ==============================
# COMPARE TARGET DISTRIBUTION
# ==============================

print("\nTraining actual demand:")
print(train_df["actual_demand_l"].describe())

print("\nTesting actual demand:")
print(test_df["actual_demand_l"].describe())


# ==============================
# PHASE 10: BASELINE MODEL
# LINEAR REGRESSION
# ==============================

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Create Linear Regression model
linear_model = LinearRegression()

# Train the model
linear_model.fit(X_train_scaled, y_train)

# Predict June demand
linear_predictions = linear_model.predict(X_test_scaled)

# Calculate metrics
linear_mae = mean_absolute_error(y_test, linear_predictions)
linear_rmse = np.sqrt(mean_squared_error(y_test, linear_predictions))
linear_mape = np.mean(
    np.abs((y_test.values - linear_predictions) / y_test.values)
) * 100

print("\n==============================")
print("LINEAR REGRESSION RESULTS")
print("==============================")

print(f"MAE:  {linear_mae:,.2f} litres")
print(f"RMSE: {linear_rmse:,.2f} litres")
print(f"MAPE: {linear_mape:.2f}%")

print("\nFirst 10 predictions:")
print(linear_predictions[:10])

print("\nFirst 10 actual values:")
print(y_test.values[:10])

# ==============================
# PHASE 10.2: RANDOM FOREST
# ==============================

from sklearn.ensemble import RandomForestRegressor

# Create Random Forest model
rf_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

# Train the model
rf_model.fit(X_train_scaled, y_train)

# Predict June demand
rf_predictions = rf_model.predict(X_test_scaled)

# Calculate metrics
rf_mae = mean_absolute_error(y_test, rf_predictions)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_predictions))
rf_mape = np.mean(
    np.abs((y_test.values - rf_predictions) / y_test.values)
) * 100

print("\n==============================")
print("RANDOM FOREST RESULTS")
print("==============================")

print(f"MAE:  {rf_mae:,.2f} litres")
print(f"RMSE: {rf_rmse:,.2f} litres")
print(f"MAPE: {rf_mape:.2f}%")

print("\nFirst 10 predictions:")
print(rf_predictions[:10])

print("\nFirst 10 actual values:")
print(y_test.values[:10])

# ==============================
# PHASE 10.3: GRADIENT BOOSTING
# ==============================

from sklearn.ensemble import GradientBoostingRegressor

# Create Gradient Boosting model
gb_model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    random_state=42
)

# Train the model
gb_model.fit(X_train_scaled, y_train)

# Predict June demand
gb_predictions = gb_model.predict(X_test_scaled)

# Calculate metrics
gb_mae = mean_absolute_error(y_test, gb_predictions)
gb_rmse = np.sqrt(mean_squared_error(y_test, gb_predictions))
gb_mape = np.mean(
    np.abs((y_test.values - gb_predictions) / y_test.values)
) * 100

print("\n==============================")
print("GRADIENT BOOSTING RESULTS")
print("==============================")

print(f"MAE:  {gb_mae:,.2f} litres")
print(f"RMSE: {gb_rmse:,.2f} litres")
print(f"MAPE: {gb_mape:.2f}%")

print("\nFirst 10 predictions:")
print(gb_predictions[:10])

print("\nFirst 10 actual values:")
print(y_test.values[:10])

# ==============================
# PHASE 10.4: LSTM
# ==============================

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# Number of previous days used to predict the next day
sequence_length = 7

# Create sequences separately for each village
X_lstm = []
y_lstm = []
dates_lstm = []

for village_id, village_data in df.groupby("village_id"):

    village_data = village_data.sort_values("date")

    village_X = village_data[features].values
    village_y = village_data[target].values
    village_dates = village_data["date"].values

    for i in range(sequence_length, len(village_data)):
        X_lstm.append(village_X[i-sequence_length:i])
        y_lstm.append(village_y[i])
        dates_lstm.append(village_dates[i])

X_lstm = np.array(X_lstm)
y_lstm = np.array(y_lstm)
dates_lstm = np.array(dates_lstm)

print("\nLSTM dataset shape:")
print("X:", X_lstm.shape)
print("y:", y_lstm.shape)

# Split according to date
train_mask = dates_lstm < np.datetime64("2025-06-01")
test_mask = dates_lstm >= np.datetime64("2025-06-01")

X_lstm_train = X_lstm[train_mask]
y_lstm_train = y_lstm[train_mask]

X_lstm_test = X_lstm[test_mask]
y_lstm_test = y_lstm[test_mask]

# Scale LSTM features
lstm_mean = X_lstm_train.reshape(-1, len(features)).mean(axis=0)
lstm_std = X_lstm_train.reshape(-1, len(features)).std(axis=0)

lstm_std[lstm_std == 0] = 1

X_lstm_train = (
    X_lstm_train - lstm_mean
) / lstm_std

X_lstm_test = (
    X_lstm_test - lstm_mean
) / lstm_std

# Create LSTM model
lstm_model = Sequential([
    LSTM(64, input_shape=(sequence_length, len(features))),
    Dense(32, activation="relu"),
    Dense(1)
])

lstm_model.compile(
    optimizer="adam",
    loss="mse",
    metrics=["mae"]
)

# Train
lstm_history = lstm_model.fit(
    X_lstm_train,
    y_lstm_train,
    epochs=30,
    batch_size=32,
    validation_split=0.1,
    verbose=1
)

# Predict
lstm_predictions = lstm_model.predict(
    X_lstm_test
).flatten()

# Calculate metrics
lstm_mae = mean_absolute_error(
    y_lstm_test,
    lstm_predictions
)

lstm_rmse = np.sqrt(
    mean_squared_error(
        y_lstm_test,
        lstm_predictions
    )
)

lstm_mape = np.mean(
    np.abs(
        (y_lstm_test - lstm_predictions)
        / y_lstm_test
    )
) * 100

print("\n==============================")
print("LSTM RESULTS")
print("==============================")

print(f"MAE:  {lstm_mae:,.2f} litres")
print(f"RMSE: {lstm_rmse:,.2f} litres")
print(f"MAPE: {lstm_mape:.2f}%")

print("\nFirst 10 predictions:")
print(lstm_predictions[:10])

print("\nFirst 10 actual values:")
print(y_lstm_test[:10])


# ==========================================
# PHASE 11: TIME-SERIES VALIDATION
# ==========================================

# Chronological split
train_df = df[
    (df["date"] >= "2025-04-01") &
    (df["date"] <= "2025-05-15")
]

validation_df = df[
    (df["date"] >= "2025-05-16") &
    (df["date"] <= "2025-05-31")
]

test_df = df[
    (df["date"] >= "2025-06-01") &
    (df["date"] <= "2025-06-29")
]

print("\n===== TIME-SERIES SPLIT =====")

print("Training:")
print(train_df["date"].min(), "to", train_df["date"].max())
print("Records:", len(train_df))

print("\nValidation:")
print(validation_df["date"].min(), "to", validation_df["date"].max())
print("Records:", len(validation_df))

print("\nTesting:")
print(test_df["date"].min(), "to", test_df["date"].max())
print("Records:", len(test_df))

X_train = train_df[features]
y_train = train_df[target]

X_val = validation_df[features]
y_val = validation_df[target]

X_test = test_df[features]
y_test = test_df[target]

# Calculate mean and standard deviation ONLY from training data
train_mean = X_train.mean()
train_std = X_train.std()

# Avoid division by zero
train_std[train_std == 0] = 1

# Scale all three sets using training statistics
X_train_scaled = (X_train - train_mean) / train_std
X_val_scaled = (X_val - train_mean) / train_std
X_test_scaled = (X_test - train_mean) / train_std

print("\n===== FINAL DATA SHAPES =====")

print("X_train:", X_train_scaled.shape)
print("y_train:", y_train.shape)

print("X_val:", X_val_scaled.shape)
print("y_val:", y_val.shape)

print("X_test:", X_test_scaled.shape)
print("y_test:", y_test.shape)

# ==========================================
# PHASE 11.2: VALIDATE BASELINE MODELS
# ==========================================

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np


# ---------- Linear Regression ----------

linear_model = LinearRegression()

linear_model.fit(
    X_train_scaled,
    y_train
)

linear_val_predictions = linear_model.predict(X_val_scaled)

linear_val_mae = mean_absolute_error(
    y_val,
    linear_val_predictions
)

linear_val_rmse = np.sqrt(
    mean_squared_error(
        y_val,
        linear_val_predictions
    )
)


# ---------- Random Forest ----------

rf_model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

rf_model.fit(
    X_train_scaled,
    y_train
)

rf_val_predictions = rf_model.predict(X_val_scaled)

rf_val_mae = mean_absolute_error(
    y_val,
    rf_val_predictions
)

rf_val_rmse = np.sqrt(
    mean_squared_error(
        y_val,
        rf_val_predictions
    )
)


# ---------- Gradient Boosting ----------

gb_model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    random_state=42
)

gb_model.fit(
    X_train_scaled,
    y_train
)

gb_val_predictions = gb_model.predict(X_val_scaled)

gb_val_mae = mean_absolute_error(
    y_val,
    gb_val_predictions
)

gb_val_rmse = np.sqrt(
    mean_squared_error(
        y_val,
        gb_val_predictions
    )
)


# ---------- Display Results ----------

print("\n===== VALIDATION RESULTS =====")

print("\nLinear Regression")
print("MAE :", round(linear_val_mae, 2))
print("RMSE:", round(linear_val_rmse, 2))

print("\nRandom Forest")
print("MAE :", round(rf_val_mae, 2))
print("RMSE:", round(rf_val_rmse, 2))

print("\nGradient Boosting")
print("MAE :", round(gb_val_mae, 2))
print("RMSE:", round(gb_val_rmse, 2))
# ==========================================
# PHASE 11.3: FINAL TEST
# ==========================================

# Select the best model based on validation
final_model = LinearRegression()

# Train using training data
final_model.fit(
    X_train_scaled,
    y_train
)

# Predict completely unseen test data
final_predictions = final_model.predict(X_test_scaled)

# Calculate final metrics
final_mae = mean_absolute_error(
    y_test,
    final_predictions
)

final_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        final_predictions
    )
)

final_mape = np.mean(
    np.abs(
        (y_test.values - final_predictions)
        / y_test.values
    )
) * 100

print("\n===== FINAL TEST RESULTS =====")

print("Selected Model: Linear Regression")
print("MAE :", round(final_mae, 2), "L")
print("RMSE:", round(final_rmse, 2), "L")
print("MAPE:", round(final_mape, 2), "%")