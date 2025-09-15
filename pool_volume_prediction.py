import mlflow
import mlflow.xgboost
import mlflow.lightgbm
import mlflow.sklearn

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import numpy as np

import pandas as pd
from sklearn.model_selection import train_test_split

# 1. Load your data
df = pd.read_csv(r"C:\Users\saran\OneDrive\Desktop\data_retrieval\BSC\df2.csv")
df.head()  # optional check

# 2. Define features and target
features = [
    "lag_1", "lag_7", "roll_mean_7", "roll_std_7",
    "price_lag_1", "day_of_week", "lag_2",
    "log_volume_diff_1", "price_std_7", "roll_max_7",
    "roll_mean_7_by_roll_std_7"
]
target = "log_volume"

# 3. Drop rows with NaN (due to shifting or rolling)
df = df.dropna(subset=features + [target]).reset_index(drop=True)

# 4. Split into train/test using time-based split
#    Example: first 85% of data → train, remaining → test
train_size = int(len(df) * 0.85)
train = df.iloc[:train_size].copy()
test = df.iloc[train_size:].copy()

# 1. Point MLflow to your tracking server
mlflow.set_tracking_uri("http://localhost:5000")

# 2. Set an experiment
mlflow.set_experiment("Volume_Prediction_Models")

# 3. Enable auto-logging for your frameworks
mlflow.xgboost.autolog()
mlflow.lightgbm.autolog()
mlflow.sklearn.autolog()

# 4. Define your models
models = {
    "xgb": XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42),
    "lgbm": LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42),
    "rf": RandomForestRegressor(n_estimators=300, max_depth=6, min_samples_leaf=4, max_features='sqrt', random_state=42, n_jobs=-1)
}

# 5. Train, predict, and log metrics per model
for name, model in models.items():
    with mlflow.start_run(run_name=name):
        model.fit(train[features], train[target])
        preds = model.predict(test[features])
        rmse = np.sqrt(mean_squared_error(test[target], preds))
        mlflow.log_metric("rmse", rmse)
        print(f"{name.upper()} RMSE: {rmse:.4f}")
