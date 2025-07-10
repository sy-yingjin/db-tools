# QAQC Scripts Guide
This document is to explain and navigate the QAQC scripts in detail.

## QAQC Scripts:
Supporting imports are needed from other files like `db.py` to be able to use some of these scripts. Other files like the `qc2_config.csv` file is needed to comfortably implement quick changes to the climate's limits.

These scripts assumes that the appropriate changes are done to the *table name(s)* and *column list(s)* in the scripts.

Additionally, all of the scripts require the arguments `{yyyy}` and `{mm}`.


### obs-qc0_splitstn.py
This file directly retreives observation data from the database and divides the observations to per-stations. Also collects an updated list of logged automated weather stations.

> *Returns:*
> - `stn-type.csv` -- a file that contains every station's ID, name, and type (Lufft or Davis).
> - `observation-{yyyy}{mm}-{station_id}.csv` -- N files of every observation for the indicated year and month where N is the number of stations found in `stn-type.csv`.

> Supporting files include:
> - `db.py` -- for functions `get_stn()` and `get_data()`
>   - `get_data()` arguments: {tablename: str}, start_date: {timestamp}, end_date {timestamp}

### obs-qc1_missing.py
This file checks the completeness of the observations from each station, as per the World Meteorological Organization's standard.

> *Returns*
> - `observation-{yyyy}{mm}-obs_log.csv` -- a file that contains the columns:
>   - `qc1-missing_perc`
>   - `qc1-expected_obs`
>   - `qc1-actual_obs`

> Supporting files include:
> - `stn-type.csv` -- for identifying the station type of each station to know what columns they have in the file

### obs-qc2_values.py
This file checks the validity and the cohesion of the data. Testing the validity requires the help of a supporting file that sets the limits of each column. Testing the cohesion requires more flexibility since not all cohesive tests are equal or always conditionally similar.

> *Returns*
> - `observation-{yyyy}{mm}-obs_log.csv` -- a file that contains the columns:
>   - `id`
>   - `timestamp`
>   - `flagged-error`
>   - `qc2-flagged_var`
>   - `qc2-flagged_data`

> Supporting files include:
> - `qc2_config.csv` -- a CSV file that allows the user to modify the limits of any column in the database to flag any erroneous data.

### obs-qc3_hourly.py
This file converts the observation data into hourly observation reports. It returns an averaged value for every hour.
*Note that this makes some variables like `wdir` inaccurate**

> *Returns*
> - [UPDATED] `observation-{yyyy}{mm}-{station_id}.csv` -- files are updated to contain the new values made after the conversion

### obs-qc4_change.py