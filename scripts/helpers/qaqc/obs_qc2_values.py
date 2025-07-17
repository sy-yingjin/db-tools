import os
import glob
import re
import pandas as pd

from pathlib import Path


# GLOBAL VARIABLES
file_prefix = "observation"
main_dir = Path("bak")
config_dir = Path("helpers")

config_file = config_dir / "qc2_config.csv"


# get the configuration for min-max values
def get_minmax(file: Path | None = None) -> dict[str, int | int] | None:
    """SUMMARY:
    With a file, get the minimum and maximum
    values allowable for all the listed columns.

    Raises:
        FileNotFoundError: Script can't find the config_file
    """
    try:
        # Error Handling #1
        if file is None:
            file = config_file
            if config_file is None:
                print("FileNotFoundError: `qc2_config.csv` can't be located.")
                return None

        # extract data from csv
        config_df = pd.read_csv(file, usecols=["var", "min", "max"])
        config_df = config_df.set_index("var")
        test_dict = config_df.to_dict(orient="index")
        out_dict = {key: list(value.values()) for key, value in test_dict.items()}
        return out_dict

    except Exception as e:
        print("Something went wrong with getting the MinMax of Range Checking")
        print(f"The exception is: {e}")


def get_range(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame, file: Path | None = None
) -> pd.DataFrame:
    """SUMMARY:
    Scans the observation CSV files and checks
    if the data is within the valid range.
    Returns the flagged data in the `check_df`.
    """
    try:
        minmax = get_minmax(file)
        if minmax is None:
            print("Without `get_minmax`, you can't conduct the range test")
            # End the function early
            return check_df

        for key in minmax.keys():
            for index, value in df.loc[
                (df[key] < minmax[key][0]) | (df[key] > minmax[key][1]), key
            ].items():
                obs_id = df["id"].get(index)

                # store data into the dataframe
                check_df.loc[-1] = [
                    2,
                    stn_id,
                    "",
                    "",
                    "",
                    obs_id,
                    index,
                    "invalid range",
                    key,
                    value,
                ]
                check_df.index += 1
                check_df.sort_index
        return check_df

    except Exception as e:
        print("Something went wrong with testing the range")
        print(f"The exception is: {e}")


def get_logic_srad(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame
) -> pd.DataFrame:
    """SUMMARY:
    Checks the cohesion of `srad` with the time.
    Solar Radiation shouldn't be detected at Night (7pm-5am).

    Raises:
        ValueError: SRAD isn't found in the columns.
    """
    try:
        # Error Handling #1
        if "srad" not in df.columns:
            print("ValueError: SRAD doesn't exist in the DataFrame")
            # End the function early
            return check_df

        for index, value in df.loc[
            (df["srad"] > 0) & ((df.index.hour > 18) | (df.index.hour < 5)), "srad"
        ].items():
            obs_id = df["id"].get(index)

            # store data into the dataframe
            check_df.loc[-1] = [
                2,
                stn_id,
                "",
                "",
                "",
                obs_id,
                index,
                "incohesive data",
                "srad",
                value,
            ]
            check_df.index += 1
            check_df.sort_index
        return check_df

    except Exception as e:
        print("Something went wrong with checking srad at night")
        print(f"The exception is: {e}")


def get_logic_rh(df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame) -> pd.DataFrame:
    """SUMMARY
    Checks the cohesion of `rh` with the temperature
    and rainfall rate.
    The Relative Humidity shouldn't be at 99 if there was
    no rain and a high difference in temperature and dewpoint.

    Raises:
        ValueError: RH isn't found in the columns
    """
    try:
        # Error Handling #1
        if "rh" not in df.columns:
            print("ValueError: RH doesn't exist in the DataFrame")
            # End the function early
            return check_df

        for index, value in df.loc[
            ((df["temp"] - df["td"]) <= 0.2) & (df["rh"] == 99) & (df["rr"] == 0), "rh"
        ].items():
            obs_id = df["id"].get(index)

            # store data into the dataframe
            check_df.loc[-1] = [
                2,
                stn_id,
                "",
                "",
                "",
                obs_id,
                index,
                "incohesive data",
                "rh",
                value,
            ]
            check_df.index += 1
            check_df.sort_index
        return check_df

    except Exception as e:
        print("Something went wrong with checking rh when there is no rain")
        print(f"The exception is: {e}")


def get_logic_wdir(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame
) -> pd.DataFrame:
    """SUMMARY:
    Checks the cohesion of `wdir` with the wind speed.
    Wind Direction should be NaN or Empty if wind speed is 0.

    Raises:
        ValueError: WDIR isn't found in the columns
    """
    try:
        # Error Handling #1
        if "wdir" not in df.columns:
            print("ValueError: WDIR doesn't exist in the DataFrame")
            # End the function early
            return check_df

        for index, value in df.loc[
            (df["wdir"].notna()) & (df["wspd"] == 0), "wdir"
        ].items():
            obs_id = df["id"].get(index)

            # store data into the dataframe
            check_df.loc[-1] = [
                2,
                stn_id,
                "",
                "",
                "",
                obs_id,
                index,
                "incohesive data",
                "wdir",
                value,
            ]
            check_df.index += 1
            check_df.sort_index
        return check_df

    except Exception as e:
        print("Something went wrong with checking wdir when there's no wspd")
        print(f"The exception is: {e}")


def qc2_values(yyyy: int, mm: int):
    # get files from monthly directory
    files = glob.glob(os.path.join(main_dir, f"{yyyy}/{mm}/*.csv"))

    # get the previous log data csv
    check_file = main_dir / f"{yyyy}/obs_logs/{file_prefix}-{yyyy}{mm}-log.csv"

    # extract data from csv
    check_df = pd.read_csv(
        check_file,
        usecols=[
            "qc_level",
            "stn_id",
            "qc1-missing_perc",
            "qc1-expected_obs",
            "qc1-actual_obs",
        ],
    )
    # create new columns for qc2
    check_df["id"] = ""
    check_df["timestamp"] = ""
    check_df["flagged_error"] = ""
    check_df["qc2-flagged_var"] = ""
    check_df["qc2-flagged_data"] = ""

    # loop through the files
    for file in files:
        df = pd.read_csv(file)

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")

        stn_id = re.findall(f"{yyyy}{mm}-([\\d]+).csv", os.path.basename(file))  # noqa: E501

        print(f"Checking validity of data from station id {stn_id[0]}...")

        """=========================================
        VALIDITY RANGE CHECKS: Checks for if the data falls within the valid data range
        will raise the `invalid range` flag

        """
        check_df = get_range(df, int(stn_id[0]), check_df, config_file)

        """=========================================
        COHESIVE LOGIC CHECKS: Checks for contradictions or logic between variables
        will raise the `incohesive data` flag
        """
        check_df = get_logic_srad(df, int(stn_id[0]), check_df)

        check_df = get_logic_rh(df, int(stn_id[0]), check_df)

        check_df = get_logic_wdir(df, int(stn_id[0]), check_df)

        # output a csv
        check_file = main_dir / f"{yyyy}/obs_logs/{file_prefix}-{yyyy}{mm}-log.csv"
        check_file.parent.mkdir(parents=True, exist_ok=True)
        check_df.to_csv(check_file, index=False)

        # mark datapoints as within valid range
        df["qc_level"] = df["qc_level"].mask(df["qc_level"] == 1, other=2)
        df.to_csv(file)
