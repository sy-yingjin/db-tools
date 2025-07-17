import os
import glob
import re
import pandas as pd

from pathlib import Path
from calendar import monthrange


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


def get_stn_type(file: Path | None = None, id: int | None = None) -> str | None:
    """SUMMARY:
    Reads the `stn-type.csv` file and returns the station-type string.

    Raises:
        FileNotFoundError: can't locate the `stn-type.csv` file
        ValueError: a station_id is unrecognized
    """
    try:
        # Error Handling #1
        if file is None:
            file = stn_file
            if stn_file is None:
                print("FileNotFoundError: `stn-type.csv` can't be located.")
                return None

        # Error Handling #2
        if id is None:
            print(f"ValueError: Unidentified Station ID: {id}")
            return None

        stn_df = pd.read_csv(stn_file, usecols=["id", "station_type"])

        aws = stn_df.loc[(stn_df["id"] == id), "station_type"].item()
        return aws

    except Exception as e:
        print("Something went wrong with getting the Station List")
        print(f"The exception is: {e}")


# get columns excluding station_id, id created_on and updated_on
def get_matching_columns(
    col_names1: list[str] | None = None, col_names2: list[str] | None = None
) -> list[str] | None:
    """SUMMARY:
    Takes in columns and compares them to
    return a list of matching column names between
    the stations, for universality.

    Raises:
        ValueError: None of the columns match
        KeyError: Required columns are missing
    """
    try:
        if col_names1 is None:
            col_names1 = COL_NAMES["davis"]
        if col_names2 is None:
            col_names2 = COL_NAMES["lufft"]

        # Error Handling #1
        col_names = [x for x in col_names1 if x in col_names2]
        if not col_names:
            print("No Matching Columns Found")
            return None

        # Error Handling #2
        necessary_cols = ["id", "timestamp", "qc_level"]
        for item in necessary_cols:
            if item not in col_names:
                print(f"Missing required column: {item}")
                return None

        return col_names

    except Exception as e:
        print("Something went wrong with finding matching columns")
        print(f"The exception is: {e}")


# find the frequency of each station type
def get_frequency(type: str) -> int | None:
    """SUMMARY:
    According to the type of station,
    returns the frequency of observations
    to be able to calculate the expected number
    of observations made in the month.

    Raises:
        ValueError: the input is not recognized
    """
    try:
        if type == "SMS":
            freq = 144
        elif type == "MO":
            freq = 288
        # Error Handling #1
        else:
            print(f"ValueError: Unidentified Station Type: {type}")
            return None

        return freq

    except Exception as e:
        print("Something went wrong with getting the frequency")
        print(f"The exception is: {e}")


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

    except Exception as e:
        print("Something went wrong with updating the CSV file")
        print(f"The exception is: {e}")


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
        if stn_type is None:
            continue

        freq = get_frequency(stn_type)
        if freq is None:
            continue

        # !! Temporary Solution until Station 36 figures it out
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
