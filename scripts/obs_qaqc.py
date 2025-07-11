import sys
import pandas as pd
from datetime import datetime


from helpers.qaqc import obs_qc0_splitstn
from helpers.qaqc import obs_qc1_missing
from helpers.qaqc import obs_qc2_values
from helpers.qaqc import obs_qc3_hourly
from helpers.qaqc import obs_qc4_change


def help_message(nargs: int):
    if nargs == 0:
        print("missing `year` parameter")
    if nargs < 2:
        print("missing `month` parameter")
    print(f"{sys.argv[0]} yyyy mm")
    sys.exit(2)


def validate_request(yyyy: int, mm: int):
    input_date = pd.to_datetime(
        datetime.strptime(f"{yyyy}-{mm}-01", "%Y-%m-%d")
    ).tz_localize("Asia/Manila")
    current_date = pd.to_datetime(datetime.now()).tz_localize("Asia/Manila")
    lim_date = pd.to_datetime(datetime.strptime("2010-01-01", "%Y-%m-%d")).tz_localize(
        "Asia/Manila"
    )

    date_check = (input_date < lim_date) or (input_date > current_date)

    if date_check:
        print("The requested `yyyy` and `mm` isn't possible.")
        sys.exit(2)


def main():
    yyyy = sys.argv[1]
    mm = sys.argv[2]

    # is the requested year and month valid?
    validate_request(yyyy, mm)

    try:
        print("\nRunning QC0 = Splitting Stations Script... \n")
        # make a list of stations with their ids and types
        obs_qc0_splitstn.get_stations()
        obs_qc0_splitstn.split_station(yyyy, mm)

        print("\nRunning QC1 = Getting Missing Percentage Script... \n")
        obs_qc1_missing.main_qc1(yyyy, mm)

        print("\nRunning QC2 = Confirming Observation Values Script... \n")
        obs_qc2_values.qc2_values(yyyy, mm)

        print("\nRunning QC3 = Converting Data to Hourly Reports Scipt... \n")
        obs_qc3_hourly.qc3_hourly(yyyy, mm)

        print("\nRunning QC4 = Comparing Data Between Hours... \n")
        obs_qc4_change.qc4_change(yyyy, mm)

    except NameError:
        print("One of the QAQC scripts is missing or not working.")
    except Exception as e:  # noqa: E722
        print(f"The exception is: {e}")
        print("One of the QAQC scripts didn't run properly.")


if __name__ == "__main__":
    nargs = len(sys.argv[1:])
    if nargs != 2:
        help_message(nargs)

    main()
