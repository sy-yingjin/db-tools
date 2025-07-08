import os
import glob
import re
import pandas as pd

from pathlib import Path
from calendar import monthrange


# Prerequisite/s: `obs_qc0_splitstn.py`

# GLOBAL VARIABLES
file_prefix = "observation"
main_dir = Path("bak")

stn_file = main_dir / "stn-type.csv"

COL_NAMES = {
    "davis": [
        "timestamp",
        "id",
        "qc_level",
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
    ],
    "lufft": [
        "timestamp",
        "id",
        "qc_level",
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
    ],
}


def get_stn_type(stn_file: Path, id: int) -> str:
    try:
        # extract data from stn csv
        stn_df = pd.read_csv(stn_file, usecols=["id", "station_type"])
        if id not in stn_df["id"].to_numpy(dtype=int):
            raise ValueError
        aws = stn_df.loc[(stn_df["id"] == id), "station_type"].item()
        return aws

    except FileNotFoundError:
        print("Can't locate the Station List file")
    except ValueError:
        print("Unrecognized Station ID Found")
    except:  # noqa: E722
        print("Something went wrong with getting the Station List")


# get columns excluding station_id, id created_on and updated_on
def get_matching_columns(
    col_names1: list[str] | None = None, col_names2: list[str] | None = None
) -> list[str] | None:
    if col_names1 is None:
        col_names1 = COL_NAMES["davis"]
    if col_names2 is None:
        col_names2 = COL_NAMES["lufft"]

    # matching column data
    col_names = [x for x in col_names1 if x in col_names2]
    if not col_names:
        print("No Matching Columns Found")
        return None

    # Columns that are needed for the script to function
    necessary_cols = ["id", "timestamp", "qc_level"]
    for item in necessary_cols:
        if item not in col_names:
            print(f"Missing required column: {item}")
            return None

    return col_names


# find the frequency of each station type
def get_frequency(type: str) -> int:
    try:
        if type == "SMS":
            freq = 144
        elif type == "MO":
            freq = 288
        else:
            raise ValueError
        return freq

    except ValueError:
        print("Unidentified Station Type")
    except:  # noqa: E722
        print("Something went wrong with getting the frequency")


def set_timestamp(file: Path, col_names: list[str]) -> pd.DataFrame:
    try:
        df = pd.read_csv(file, usecols=col_names)
        df = df[col_names]
        df["qc_level"] = 1
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        # converts utc -> local time
        df = df.tz_convert("Asia/Manila")
        df.to_csv(file)
        return df

    except:  # noqa: E722
        print("Something went wrong with updating the CSV file")


def main_qc1(yyyy: int, mm: int):
    # get files from monthly directory
    files = glob.glob(os.path.join(main_dir, f"{yyyy}/{mm}/*.csv"))

    check_df = pd.DataFrame(
        columns=[
            "qc_level",
            "stn_id",
            "qc1-missing_perc",
            "qc1-expected_obs",
            "qc1-actual_obs",
        ]
    )

    # get the number of days in the month
    ndays = monthrange(int(yyyy), int(mm))[1]

    # loop through files
    for file in files:
        stn_id = re.findall(f"{yyyy}{mm}-([\\d]+).csv", os.path.basename(file))  # noqa: E501

        print(f"Checking observation data of station id {stn_id[0]}...")

        # get matching columns
        col_names = get_matching_columns()
        if col_names is None:
            continue
        obs_df = set_timestamp(file, col_names)

        stn_type = get_stn_type(stn_file, int(stn_id[0]))
        freq = get_frequency(stn_type)

        # !! EXCEPTION: Temporary Solution until Station 36 figures it out
        if int(stn_id[0]) == 36:
            freq = 144

        # MISSING CHECK
        expected_obs = ndays * freq
        actual_obs = len(obs_df)
        missing = expected_obs - actual_obs
        missing_perc = missing / expected_obs * 100

        # store check data into the check_df
        check_df.loc[-1] = [
            1,
            stn_id[0],
            round(missing_perc, 2),
            expected_obs,
            actual_obs,
        ]
        check_df.index += 1
        check_df.sort_index

    # output the check_df into a csv file
    check_file = main_dir / f"{yyyy}/obs_logs/{file_prefix}-{yyyy}{mm}-log.csv"
    check_file.parent.mkdir(parents=True, exist_ok=True)
    check_df.to_csv(check_file, index=False)
