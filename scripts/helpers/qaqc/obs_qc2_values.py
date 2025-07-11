import os
import glob
import re
import pandas as pd

from pathlib import Path


# Prerequisite/s: `obs_qc0_splitstn.py`

# GLOBAL VARIABLES
file_prefix = "observation"
main_dir = Path("bak")
config_dir = Path("helpers")

config_file = config_dir / "qc2_config.csv"


# get the configuration for min-max values
def get_minmax(config_file: Path) -> dict[str, int | int]:
    try:
        # extract data from csv
        config_df = pd.read_csv(config_file, usecols=["var", "min", "max"])
        config_df = config_df.set_index("var")
        test_dict = config_df.to_dict(orient="index")
        out_dict = {key: list(value.values()) for key, value in test_dict.items()}

        return out_dict

    except FileNotFoundError:
        print("Can't locate the Configuration file")
    except:  # noqa: E722
        print("Something went wrong with getting the MinMax of Range Checking")


def get_range(df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame) -> pd.DataFrame:
    try:
        minmax = get_minmax(config_file)
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

    except:  # noqa: E722
        print("Something went wrong with testing the range")


def get_logic_srad(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame
) -> pd.DataFrame:
    try:
        if "srad" not in df.columns:
            raise ValueError

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

    except ValueError:
        print("SRAD doesn't exist in the DataFrame")
    except:  # noqa: E722
        print("Something went wrong with checking srad at night")


def get_logic_rh(df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame) -> pd.DataFrame:
    try:
        if "rh" not in df.columns:
            raise ValueError

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

    except ValueError:
        print("RH doesn't exist in the DataFrame")
    except:  # noqa: E722
        print("Something went wrong with checking rh when there is no rain")


def get_logic_wdir(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame
) -> pd.DataFrame:
    try:
        if "wdir" not in df.columns:
            raise ValueError

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

    except ValueError:
        print("WDIR doesn't exist in the DataFrame")
    except:  # noqa: E722
        print("Something went wrong with checking wdir when there's no wspd")


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
        check_df = get_range(df, int(stn_id[0]), check_df)

        """=========================================
        COHESIVE LOGIC CHECKS: Checks for contradictions or logic between variables
        will raise the `incohesive data` flag
        """
        # Solar Radiation detected at night:
        check_df = get_logic_srad(df, int(stn_id[0]), check_df)

        # Humidity is at 99% without rainfall and (temp-td) is less than 0.2
        check_df = get_logic_rh(df, int(stn_id[0]), check_df)

        # Wind Direction exists when Wind Speed is 0
        check_df = get_logic_wdir(df, int(stn_id[0]), check_df)

        # output a csv
        check_file = main_dir / f"{yyyy}/obs_logs/{file_prefix}-{yyyy}{mm}-log.csv"
        check_file.parent.mkdir(parents=True, exist_ok=True)
        check_df.to_csv(check_file, index=False)

        # mark datapoints as within valid range
        df["qc_level"] = df["qc_level"].mask(df["qc_level"] == 1, other=2)
        df.to_csv(file)
