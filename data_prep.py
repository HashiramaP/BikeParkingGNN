import pandas as pd
import json
from tqdm import tqdm

# Load trips
trips = pd.read_csv("data/bixi_trajets.csv")

# Convert timestamps from ms to datetime
trips['start_time'] = pd.to_datetime(trips['STARTTIMEMS'], unit='ms')
trips['end_time'] = pd.to_datetime(trips['ENDTIMEMS'], unit='ms')

# Load stations
with open("data/station_information.json") as f:
    stations_data = json.load(f)

stations = pd.DataFrame(stations_data['data']['stations'])
stations['station_id'] = stations['station_id'].astype(str)

time_freq = '15min'
start_time = trips['start_time'].min().floor('15min')
end_time = trips['end_time'].max().ceil('15min')
time_index = pd.date_range(start=start_time, end=end_time, freq=time_freq)

occupancy = pd.DataFrame(0, index=stations['station_id'], columns=time_index)


# Map station names to station_id
station_name_to_id = dict(zip(stations['name'], stations['station_id']))

for idx, row in tqdm(trips.iterrows(), total=len(trips)):
    start_station = station_name_to_id.get(row['STARTSTATIONNAME'])
    end_station = station_name_to_id.get(row['ENDSTATIONNAME'])
    
    # Skip if stations not found
    if start_station is None or end_station is None:
        continue
    
    # Find time slots affected
    start_slot = occupancy.columns.get_indexer([row['start_time']], method='nearest')[0]
    end_slot = occupancy.columns.get_indexer([row['end_time']], method='nearest')[0]
    
    # Decrease occupancy for start station at the start slot
    occupancy.loc[start_station, occupancy.columns[start_slot]:] -= 1
    occupancy.loc[end_station, occupancy.columns[end_slot]:] += 1


for station_id in stations['station_id']:
    cap = stations.loc[stations['station_id'] == station_id, 'capacity'].values[0]
    occupancy.loc[station_id] = occupancy.loc[station_id].clip(lower=0, upper=cap)

occupancy.to_csv("data/occupancy.csv")
