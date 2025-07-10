import pytest
import pandas as pd

from helpers.qaqc.obs_qc1_missing import (
    get_stn_type,
    get_matching_columns,
    get_frequency,
    set_timestamp,
)


@pytest.fixture
def mock_stn_df():
    return pd.DataFrame({"id": [9, 5001], "station_type": ["SMS", "MO"]})


@pytest.fixture
def mock_timestamp_df():
    return pd.DataFrame(
        {
            "timestamp": ["2023-02-01 00:00:00+00:00", "2023-02-02 00:00:00+00:00"],
            "qc_level": [0, 0],
        }
    )


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
