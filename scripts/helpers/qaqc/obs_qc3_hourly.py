import os
import glob
import re
import pandas as pd

from pathlib import Path


# GLOBAL VARIABLES
main_dir = Path("bak")


# get columns excluding station_id, id created_on and updated_on
def get_matching_columns() -> list[str]:
    # The observation data is from a Davis AWS
    col_MO = [
        "timestamp",
        "pres",
        "rr",
        "rh",
        "temp",
        "td",
        "wdir",
        "wspd",
        "wspdx",
        "srad",
        "hi",
        "wchill",
        "rain",
        "tx",
        "tn",
        "wrun",
        "thwi",
        "thswi",
        "senergy",
        "sradx",
        "uvi",
        "uvdose",
        "uvx",
        "hdd",
        "cdd",
        "et",
        "wdirx",
    ]
    # The observation data is from a Lufft AWS
    col_SMS = [
        "timestamp",
        "pres",
        "rr",
        "rh",
        "temp",
        "td",
        "wdir",
        "wspd",
        "wspdx",
        "srad",
        "mslp",
        "hi",
        "wchill",
    ]

    try:
        # matching column data
        col_names = [x for x in col_MO if x in col_SMS]
        # Columns that are needed for the script to function
        necessary_cols = [
            "timestamp",
        ]
        for item in necessary_cols:
            if item not in col_names:
                raise ValueError
        if len(col_names) == 0:
            raise KeyError
        return col_names

    except ValueError:
        print("No Matching Columns Found: Missing Expected Columns")
    except KeyError:
        print("No Matching Columns Found: Empty CSV")
    except:  # noqa: E722
        print("Something went wrong with getting matching columns")


# Running this file will before qc1 and qc2 will make their reports inaccurate
def qc3_hourly(yyyy, mm):
    # get files from monthly directory
    files = glob.glob(os.path.join(main_dir, f"{yyyy}/{mm}/*.csv"))

    # loop through the files
    for file in files:
        stn_id = re.findall(f"{yyyy}{mm}-([\\d]+).csv", os.path.basename(file))  # noqa: E501

        print(f"Converting data to hourly reports for station id {stn_id[0]}...")

        # get matching columns
        col_names = get_matching_columns()

        df = pd.read_csv(file, usecols=col_names)
        df = df[col_names]
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Sort the main observation dataframe to an hourly state
        # all observations will be averaged
        hourly_df = (
            df.groupby(pd.Grouper(key="timestamp", freq="h"))[col_names[1:]]
            .mean()
            .round(2)
        )
        hourly_df.insert(0, "qc_level", 3)

        # output a csv
        hourly_df.to_csv(file)
