import pandas as pd
import numpy as np
import json
from scipy.spatial import cKDTree

# -----------------------------
# 1️⃣ Load data
# -----------------------------
df = pd.read_csv("data/bixi_trajets.csv")

with open("data/station_information.json") as f:
    stations_data = json.load(f)
stations_info = pd.DataFrame(stations_data["data"]["stations"])

# -----------------------------
# 2️⃣ Build KDTree for station coordinates
# -----------------------------
station_coords = stations_info[["lat", "lon"]].to_numpy()
tree = cKDTree(station_coords)

# -----------------------------
# 3️⃣ Map start stations
# -----------------------------
# Only keep trips with valid start coordinates
df_start_valid = df[np.isfinite(df["STARTSTATIONLATITUDE"]) & np.isfinite(df["STARTSTATIONLONGITUDE"])].copy()

trip_coords_start = df_start_valid[["STARTSTATIONLATITUDE", "STARTSTATIONLONGITUDE"]].to_numpy()
_, idxs_start = tree.query(trip_coords_start, k=1)

df_start_valid["start_station_id"] = stations_info.loc[idxs_start, "station_id"].values
df_start_valid["start_station_name"] = stations_info.loc[idxs_start, "name"].values
df_start_valid["start_capacity"] = stations_info.loc[idxs_start, "capacity"].values

# Merge back into full df
df = df.merge(
    df_start_valid[["start_station_id", "start_station_name", "start_capacity"]],
    left_index=True, right_index=True, how="left"
)

# -----------------------------
# 4️⃣ Map end stations
# -----------------------------
# Only keep trips with valid end coordinates
df_end_valid = df[np.isfinite(df["ENDSTATIONLATITUDE"]) & np.isfinite(df["ENDSTATIONLONGITUDE"])].copy()

trip_coords_end = df_end_valid[["ENDSTATIONLATITUDE", "ENDSTATIONLONGITUDE"]].to_numpy()
_, idxs_end = tree.query(trip_coords_end, k=1)

df_end_valid["end_station_id"] = stations_info.loc[idxs_end, "station_id"].values
df_end_valid["end_station_name"] = stations_info.loc[idxs_end, "name"].values
df_end_valid["end_capacity"] = stations_info.loc[idxs_end, "capacity"].values

# Merge back into full df
df = df.merge(
    df_end_valid[["end_station_id", "end_station_name", "end_capacity"]],
    left_index=True, right_index=True, how="left"
)

# -----------------------------
#  Optional: check examples of missing mapping
# -----------------------------
print("Trips with missing start station mapping:", df["start_station_id"].isna().sum())
print("Trips with missing end station mapping:", df["end_station_id"].isna().sum())
print("Example missing end station trip:")
print(df[df["end_station_id"].isna()].head(1))
# -----------------------------
# 5️⃣ Prepare departures and arrivals
# -----------------------------
TIME_FREQ = "15min"

# Convert timestamps if not done yet
df["start_time"] = pd.to_datetime(df["STARTTIMEMS"], unit="ms")
df["end_time"] = pd.to_datetime(df["ENDTIMEMS"], unit="ms")

valid_trips = df.dropna(subset=["start_station_id", "end_station_id"])
departures = (
    valid_trips.groupby([pd.Grouper(key="start_time", freq=TIME_FREQ), "start_station_id"])
    .size().reset_index(name="nb_depart")
)
arrivals = (
    valid_trips.groupby([pd.Grouper(key="end_time", freq=TIME_FREQ), "end_station_id"])
    .size().reset_index(name="nb_arrivee")
)


# Rename columns for merging
departures.rename(columns={"start_station_id": "station_id", "start_time": "datetime"}, inplace=True)
arrivals.rename(columns={"end_station_id": "station_id", "end_time": "datetime"}, inplace=True)

# -----------------------------
# 6️⃣ Fusion et remplissage des horaires manquants
# -----------------------------
all_times = pd.date_range(df["start_time"].min(), df["end_time"].max(), freq=TIME_FREQ)
stations = stations_info["station_id"].unique()
index = pd.MultiIndex.from_product([stations, all_times], names=["station_id", "datetime"])

station_activity = pd.merge(departures, arrivals, on=["station_id", "datetime"], how="outer").fillna(0)
station_activity = (
    station_activity.set_index(["station_id", "datetime"])
    .reindex(index, fill_value=0)
    .reset_index()
)

# Add name and capacity
station_activity = station_activity.merge(
    stations_info[["station_id", "name", "capacity"]], on="station_id", how="left"
)
station_activity.rename(columns={"name": "station_name"}, inplace=True)

# -----------------------------
# 7️⃣ Calcul du delta et nb_bikes_estime
# -----------------------------
station_activity["delta"] = station_activity["nb_arrivee"] - station_activity["nb_depart"]
station_activity["nb_bikes_estime"] = (
    station_activity.groupby("station_id")["delta"].cumsum() + station_activity["capacity"] * 0.5
)
station_activity["taux_occupation"] = (station_activity["nb_bikes_estime"] / station_activity["capacity"]).clip(0, 1)

# -----------------------------
# 8️⃣ Export final CSV
# -----------------------------
station_activity.to_csv("data/bixi_taux_occupation.csv", index=False)
print("✅ Fichier exporté : data/bixi_taux_occupation.csv")
