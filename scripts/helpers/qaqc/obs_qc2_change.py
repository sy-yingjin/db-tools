import os
import glob
import re
import pandas as pd

from pathlib import Path


# GLOBAL VARIABLES
file_prefix = "observation"
main_dir = Path("bak")
config_dir = Path.cwd().parent

config_greater_file = config_dir / "config/qc2_config_greater.csv"
config_lesser_file = config_dir / "config/qc2_config_lesser.csv"
config_sd_file = config_dir / "config/qc2_config_sd.csv"


def get_config(config_file: Path) -> dict[str, int, int]:
    """SUMMARY:
    With the file, get the period and differences to flag
    if the data is invalid.
    """
    try:
        config_df = pd.read_csv(config_file, usecols=["var", "period", "diff"])
        config_dict = {key: [str, int, int] for key in range(len(config_df))}
        for key in config_dict.keys():
            name = config_df.at[key, "var"]
            period = config_df.at[key, "period"]
            diff = config_df.at[key, "diff"]

            config_dict[key] = name, period, diff
        return config_dict

    except Exception as e:
        print("Something went wrong with getting the configuration file of QC4")
        print(f"The exception is: {e}")


def get_greater_diff(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame
) -> pd.DataFrame:
    """SUMMARY:
    Using the `get_config()` function, gets its configuration
    file's values and compares them to the DataFrame.
    This Function is specifically to flag observation data that's change is too great.
    """
    try:
        # Error Handling #1
        if config_greater_file is None:
            print(
                "FileNotFoundError: The Configuration File for flagging greater values is missing."
            )
            # End the function early
            return check_df

        diff_dict = get_config(config_greater_file)

        for key in diff_dict.keys():
            variable = diff_dict[key][0]
            period = diff_dict[key][1]
            diff = diff_dict[key][2]

            diff_df = df[variable].diff(periods=period)
            for index, value in diff_df[(diff_df > diff) | (diff_df < -diff)].items():
                # store data into the dataframe
                check_df.loc[-1] = [
                    4,
                    stn_id,
                    "",
                    "",
                    "",
                    "",
                    index,
                    "invalid rate",
                    "",
                    "",
                    variable,
                    round(value, 2),
                    f"< {diff}",
                ]
                check_df.index += 1
                check_df.sort_index
        return check_df

    except Exception as e:
        print("Something went wrong with testing the greater than change rate")
        print(f"The exception is: {e}")


def get_lesser_diff(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame
) -> pd.DataFrame:
    """SUMMARY:
    Using the `get_config()` function, gets its configuration
    file's values and compares them to the DataFrame.
    This Function is specifically to flag observation data that's change is too less.
    """
    try:
        # Error Handling #1
        if config_lesser_file is None:
            print(
                "FileNotFoundError: The Configuration File for flagging lesser values is missing."
            )
            # End the function early
            return check_df

        diff_dict = get_config(config_lesser_file)

        for key in diff_dict.keys():
            variable = diff_dict[key][0]
            period = diff_dict[key][1]
            diff = diff_dict[key][2]

            diff_df = df[variable].diff(periods=period)
            for index, value in diff_df[(diff_df < diff) | (diff_df > -diff)].items():
                # store data into the dataframe
                check_df.loc[-1] = [
                    4,
                    stn_id,
                    "",
                    "",
                    "",
                    "",
                    index,
                    "invalid rate",
                    "",
                    "",
                    variable,
                    round(value, 2),
                    f"> {diff}",
                ]
                check_df.index += 1
                check_df.sort_index

        return check_df

    except Exception as e:
        print("Something went wrong with testing the lesser than change rate")
        print(f"The exception is: {e}")


def get_standard_dev(
    df: pd.DataFrame, stn_id: int, check_df: pd.DataFrame, length: int
) -> pd.DataFrame:
    """SUMMARY:
    Using the `get_config()` function, gets its configuration
    file's values and compares them to the DataFrame.
    This Function is specifically to flag observation data that's too far from the general mean.
    """
    try:
        if config_sd_file is None:
            print(
                "FileNotFoundError: The Configuration File for flagging SD values is missing."
            )
            # End the function early
            return check_df

        df_temp = df.reset_index()
        df_temp.rename(columns={"index": "timestamp"})
        sd_dict = get_config(config_sd_file)

        for key in sd_dict.keys():
            variable = sd_dict[key][0]
            period = sd_dict[key][1]
            diff = sd_dict[key][2]

            if length - period < 0:
                continue

            for x in range(length - period):
                y = x + period
                result_sd = df_temp[variable].loc[x:y].std(skipna=True)

                if result_sd < diff:
                    # store data into the dataframe
                    check_df.loc[-1] = [
                        4,
                        stn_id,
                        "",
                        "",
                        "",
                        "",
                        df_temp.at[x, "timestamp"],
                        "invalid std",
                        "",
                        "",
                        variable,
                        round(result_sd, 2),
                        f"> {diff}",
                    ]
                    check_df.index += 1
                    check_df.sort_index
        return check_df

    except Exception as e:
        print("Something went wrong with testing the change rate's standard deviation")
        print(f"The exception is: {e}")


def qc2_change(yyyy: int, mm: int):
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
            "qc0-missing_perc",
            "qc0-expected_obs",
            "qc0-actual_obs",
            "id",
            "timestamp",
            "flagged_error",
            "qc1-flagged_var",
            "qc1-flagged_data",
        ],
    )

    # create new columns for qc2
    check_df["qc2-flagged_var"] = ""
    check_df["qc2-flagged_data"] = ""
    check_df["qc2-excepted_data"] = ""

    # loop through the files
    for file in files:
        df = pd.read_csv(file)

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")

        obs_length = len(df)

        stn_id = re.findall(f"{yyyy}{mm}-([\\d]+).csv", os.path.basename(file))

        print(f"Checking the change rate from station id {stn_id[0]}...")

        """=========================================
        CHANGE RATE CHECKS: Checks the temporal difference or sum of variables
        will raise the `invalid_rate` flag
        """
        check_df = get_greater_diff(df, int(stn_id[0]), check_df)

        check_df = get_lesser_diff(df, int(stn_id[0]), check_df)

        if obs_length > 2:
            check_df = get_standard_dev(df, int(stn_id[0]), check_df, obs_length)

        # output a csv
        check_file = main_dir / f"{yyyy}/obs_logs/{file_prefix}-{yyyy}{mm}-log.csv"
        check_file.parent.mkdir(parents=True, exist_ok=True)
        check_df.to_csv(check_file, index=False)

        # mark datapoints as within valid range
        df["qc_level"] = df["qc_level"].mask(df["qc_level"] == 3, other=4)
        df.to_csv(file)
