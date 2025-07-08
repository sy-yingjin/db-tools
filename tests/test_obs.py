import pytest
import pandas as pd

from obs_qaqc import help_message, validate_request
from helpers.qaqc.obs_qc1_missing import (
    get_stn_type,
    get_matching_columns,
    get_frequency,
    set_timestamp,
)
from helpers.qaqc.obs_qc2_values import (
    get_minmax,
    get_range,
    get_logic_srad,
    get_logic_rh,
    get_logic_wdir,
)

""" NOTICE:
    a lot of the exception handling here is for specific errors like ValueErrors and KeyErrors.
    I haven't tested any other errors even though i have made exceptions for them in the actual functions.
"""


@pytest.fixture
def mock_stn_df():
    return pd.DataFrame({"id": [9, 5001], "station_type": ["SMS", "MO"]})


@pytest.fixture
def mock_minmax_df():
    return pd.DataFrame({"var": ["temp", "wdir"], "min": [15, 0], "max": [40, 360]})


@pytest.fixture
def mock_timestamp_df():
    return pd.DataFrame(
        {
            "timestamp": ["2023-02-01 00:00:00+00:00", "2023-02-02 00:00:00+00:00"],
            "qc_level": [0, 0],
        }
    )


@pytest.fixture
def mock_values_df():
    datasets = {
        "timestamp": [
            "2023-02-01 00:00:00+00:00",
            "2023-02-02 00:00:00+00:00",
            "2023-02-03 00:00:00+00:00",
        ],
        "temp": [20, 30, 35],
        "td": [20, 30, 35],
        "srad": [20, 40, 104],
        "pres": [992, 1000, 999],
        "rh": [32, 42, 43],
        "rr": [0, 10, 5],
        "wdir": [23, 43, None],
        "wspd": [42, 12, 0],
    }
    df = pd.DataFrame(data=datasets)
    df.set_index("timestamp")

    return df


def test_help_message_no_args(mocker, capsys):
    script_name = "script.py"
    mocker.patch("sys.argv", [script_name])
    with pytest.raises(SystemExit) as e:
        help_message(0)
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert "missing `year` parameter" in captured.out
    assert "missing `month` parameter" in captured.out
    assert f"{script_name} yyyy mm" in captured.out


def test_help_message_one_arg(mocker, capsys):
    script_name = "script.py"
    mocker.patch("sys.argv", [script_name])
    with pytest.raises(SystemExit) as e:
        help_message(1)
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert "missing `month` parameter" in captured.out
    assert f"{script_name} yyyy mm" in captured.out


def test_validate_request_failed(capsys):
    # current valid ranges: 2010+
    list_yy = [1999, 2000, 2001]
    for year in list_yy:
        with pytest.raises(SystemExit) as e:
            validate_request(year, "12")
        assert e.value.code == 2
        captured = capsys.readouterr()
        assert "The requested `yyyy` and `mm` isn't possible." in captured.out
    # valid date
    assert validate_request(2020, "02") is None


def test_get_stn_type(mocker, capsys, mock_stn_df):
    mock_df = mocker.Mock()
    mock_df = mock_stn_df
    mock_csv = mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_stn_type("dummy.csv", 9) == "SMS"
    mock_csv.assert_called_once_with("dummy.csv", usecols=["id", "station_type"])
    assert get_stn_type("dummy.csv", 5001) == "MO"

    mock_csv = mocker.patch("pandas.read_csv", side_effect=ValueError)
    assert get_stn_type("dummy.csv", 1) is None
    mock_csv = mocker.patch("pandas.read_csv", side_effect=FileNotFoundError)
    assert get_stn_type("dummy.csv", 9) is None

    captured = capsys.readouterr()
    # for ValueError
    assert "Unrecognized Station ID Found" in captured.out
    # for FNFError
    assert "Can't locate the Station List file" in captured.out


def test_get_minmax(mocker, capsys, mock_minmax_df):
    mock_df = mocker.Mock()
    mock_df = mock_minmax_df
    mock_csv = mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_minmax("dummy.csv", "temp") == [15, 40]
    mock_csv.assert_called_once_with("dummy.csv", usecols=["var", "min", "max"])
    assert get_minmax("dummy.csv", "wdir") == [0, 360]

    mock_csv = mocker.patch("pandas.read_csv", side_effect=ValueError)
    assert get_minmax("dummy.csv", "unknown") is None
    mock_csv = mocker.patch("pandas.read_csv", side_effect=FileNotFoundError)
    assert get_minmax("dummy.csv", "temp") is None

    captured = capsys.readouterr()
    # for ValueError
    assert "Unrecognized Variable Found" in captured.out
    # for FNFError
    assert "Can't locate the Configuration file" in captured.out


@pytest.mark.parametrize(
    "col_names1, col_names2, col_names_out",
    [
        (
            None,
            None,
            [
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
            ],
        ),
        (
            ["id", "qc_level", "pres", "rh"],
            ["id", "timestamp", "qc_level", "rh", "hi"],
            None,
        ),
    ],
)
def test_get_matching_columns(col_names1, col_names2, col_names_out):
    assert get_matching_columns(col_names1, col_names2) == col_names_out


def test_get_frequency(mocker, capsys):
    assert get_frequency("SMS") == 144
    assert get_frequency("MO") == 288

    mocker.patch("helpers.qaqc.obs_qc1_missing.get_frequency", side_effect=ValueError)
    assert get_frequency("unknown") is None
    captured = capsys.readouterr()
    assert "Unidentified Station Type" in captured.out


def test_set_timestamp(mocker, mock_timestamp_df):
    mock_col = []
    mock_df = mocker.Mock()
    mock_df = mock_timestamp_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert set_timestamp("dummy.csv", mock_col) is None


#  For some reason raising ValueError only returns the second exception message, so ValueError doesn't work.
#  TO-DO: Raise ValueError Message
def test_get_range(mocker, capsys, mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_range("dummy.csv", 12, "dump.csv") is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc2_values.get_range", side_effect=SystemError)
    assert get_range("dummy.csv", 12, "dump.csv") is None

    captured = capsys.readouterr()
    assert "Something went wrong with testing the range" in captured.out


#  For some reason raising ValueError only returns the second exception message, so ValueError doesn't work.
#  TO-DO: Raise ValueError Message
def test_get_logic_srad(mocker, capsys, mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_logic_srad("dummy.csv", 12, "dump.csv") is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc2_values.get_logic_srad", side_effect=SystemError)
    assert get_logic_srad("dummy.csv", 12, "dump.csv") is None

    captured = capsys.readouterr()
    assert "Something went wrong with checking srad at night" in captured.out


#  For some reason raising ValueError only returns the second exception message, so ValueError doesn't work.
#  TO-DO: Raise ValueError Message
def test_get_logic_rh(mocker, capsys, mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_logic_rh("dummy.csv", 12, "dump.csv") is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc2_values.get_logic_rh", side_effect=SystemError)
    assert get_logic_srad("dummy.csv", 12, "dump.csv") is None

    captured = capsys.readouterr()
    assert "Something went wrong with checking rh when there is no rain" in captured.out


#  For some reason raising ValueError only returns the second exception message, so ValueError doesn't work.
#  TO-DO: Raise ValueError Message
def test_get_logic_wdir(mocker, capsys, mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_logic_wdir("dummy.csv", 12, "dump.csv") is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc2_values.get_logic_wdir", side_effect=SystemError)
    assert get_logic_wdir("dummy.csv", 12, "dump.csv") is None

    captured = capsys.readouterr()
    assert (
        "Something went wrong with checking wdir when there's no wspd" in captured.out
    )
