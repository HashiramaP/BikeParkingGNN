# BIKE PARKING GNN

## Before starting

1. Create a folder ```Data``` in root

2. Go to https://bixi.com/fr/donnees-ouvertes and download 2024 data and name it ```bixi_trajets.csv```

3. Fetch the json from https://gbfs.velobixi.com/gbfs/2-2/en/station_information.json 

4. Add the two files in ```Data```

5. Downalod the requirements for python in ```requirements.txt```

5. run ```data_prep.py```

**The bixi_trajets** is a very heavy file, if you want to test your code without having to use the whole dataset, create another csv with the first 1000 lines of that csv.

### Data_prep.py

This script processes BIXI trip data and station information to compute the time-resolved occupancy of each bike station. It outputs a CSV (occupancy.csv) where each row is a station (station_id) and each column is a 15-minute time slot, showing the number of bikes available at that time.

Steps performed:

1. Loads trip history (bixi_trajets.csv) and converts timestamps from milliseconds to datetime.

2. oads station metadata (station_information.json) including capacities.

3. Initializes a zero occupancy matrix with stations as rows and time slots as columns.

4. Maps trip start/end station names to station IDs.

5. Iterates over trips to update occupancy:

    - ecreases bikes at the start station when a trip begins.

    - Increases bikes at the end station when a trip ends.

6. Clips occupancy to ensure values are between 0 and each station’s capacity.

7. Saves the resulting occupancy time series to occupancy.csv.