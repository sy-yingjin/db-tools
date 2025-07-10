import pytest

from obs_qaqc import help_message, validate_request


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
