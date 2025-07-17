import pytest
import pandas as pd


from helpers.qaqc.obs_qc1_values import (
    get_minmax,
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


def test_get_minmax(mocker, mock_minmax_df):
    mock_df = mocker.Mock()
    mock_df = mock_minmax_df
    mocker.patch("pandas.read_csv", return_value=mock_df)
    assert get_minmax("dummy.csv") == {"temp": [15, 40], "wdir": [0, 360]}
