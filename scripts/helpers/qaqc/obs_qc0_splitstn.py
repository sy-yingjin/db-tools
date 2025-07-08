import pandas as pd
import pytz

from datetime import datetime
from pathlib import Path
from calendar import monthrange
from helpers.db import get_data, get_stn

tz = pytz.timezone("Asia/Manila")


# GLOBAL VARIABLES
file_suffix = "observation"
out_dir = Path("bak")


# pull all data about the stations from the database
def get_stations():
    stn_df = get_stn()

    stn_file = out_dir / "stn-type.csv"
    stn_file.parent.mkdir(parents=True, exist_ok=True)
    stn_df.to_csv(stn_file, index=False)


def split_station(yyyy: int, mm: int):
    start_date = tz.localize(datetime.strptime(f"{yyyy}-{mm}-01", "%Y-%m-%d"))
    ndays = monthrange(int(yyyy), int(mm))[1]
    end_date = tz.localize(datetime.strptime(f"{yyyy}-{mm}-{ndays}", "%Y-%m-%d"))

    # get data from the Lufft and Davis AWS
    # stored in a list for easy iteration if there are future databases to join
    table_name = ["observations_observation", "observations_mo_observation"]
    for table in table_name:
        df = get_data(table, start_date, end_date)

        # separate each observation by their station
        unique_ids = df.station_id.unique()
        df_dict = {stn: pd.DataFrame() for stn in unique_ids}

        for key in df_dict.keys():
            # sort each station data by timestamp for easier manipulation later
            df_dict[key] = df[:][df.station_id == key]
            df_dict[key] = df_dict[key].sort_values(by="timestamp")

            # create a monthly and station directory in folder
            out_file = out_dir / f"{yyyy}/{mm}/{file_suffix}-{yyyy}{mm}-{key}.csv"

            out_file.parent.mkdir(parents=True, exist_ok=True)
            df_dict[key].to_csv(out_file, index=False)
