import pytest
import pandas as pd

from helpers.qaqc.obs_qc4_change import (
    get_config,
    get_greater_diff,
    get_lesser_diff,
    get_standard_dev
)


@pytest.fixture
def mock_config_df():
    return pd.DataFrame({
        "var": ["temp", "pres"],
        "period": [1, 12],
        "diff": [5, 6]})


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


def test_get_config(mocker, capsys, mock_config_df):
    mock_df = mocker.Mock()
    mock_df = mock_config_df
    mock_csv = mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_config("dummy.csv") == {0: ("temp", 1, 5), 1: ("pres", 12, 6)}
    mock_csv.assert_called_once_with("dummy.csv", usecols=["var", "period", "diff"])

    mock_csv = mocker.patch("pandas.read_csv", side_effect=FileNotFoundError)
    assert get_config("dummy.csv") is None

    captured = capsys.readouterr()
    assert "Can't locate the Configuration file" in captured.out


def test_get_greater_diff(mocker, capsys, mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_greater_diff("dummy.csv", 12, "dump.csv") is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc4_change.get_greater_diff", side_effect=SystemError)
    assert get_greater_diff("dummy.csv", 12, "dump.csv") is None

    captured = capsys.readouterr()
    assert "Something went wrong with testing the greater than change rate" in captured.out


def test_get_lesser_diff(mocker, capsys, mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_lesser_diff("dummy.csv", 12, "dump.csv") is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc4_change.get_lesser_diff", side_effect=SystemError)
    assert get_lesser_diff("dummy.csv", 12, "dump.csv") is None

    captured = capsys.readouterr()
    assert "Something went wrong with testing the lesser than change rate" in captured.out


def test_get_standard_dev(mocker, capsys , mock_values_df):
    mock_df = mock_values_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_standard_dev("dummy.csv", 12, "dump.csv", 54) is None

    mock_df = mock_values_df
    mocker.patch("helpers.qaqc.obs_qc4_change.get_standard_dev", side_effect=SystemError)
    assert get_standard_dev("dummy.csv", 12, "dump.csv", 54) is None

    captured = capsys.readouterr()
    assert "Something went wrong with testing the change rate's standard deviation" in captured.out