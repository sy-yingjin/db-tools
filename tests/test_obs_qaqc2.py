import pytest
import pandas as pd


from helpers.qaqc.obs_qc2_values import (
    get_minmax,
    get_range,
    get_logic_srad,
    get_logic_rh,
    get_logic_wdir,
)


@pytest.fixture
def mock_minmax_df():
    return pd.DataFrame({"var": ["temp", "wdir"], "min": [15, 0], "max": [40, 360]})


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
