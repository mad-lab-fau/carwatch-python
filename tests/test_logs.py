import shutil
import unittest.mock
import warnings
from contextlib import contextmanager
from inspect import getmembers, isfunction
from pathlib import Path
from unittest import TestCase

import numpy as np
import pandas as pd
import pytest

import carwatch.example_data
from carwatch.logs import ParticipantLogs
from carwatch.utils._datatype_validation_helper import _assert_is_dtype
from carwatch.utils.exceptions import FileExtensionError, LogDataParseError

TEST_DATA_PATH = Path(__file__).parent.joinpath("test_data")

from pandas._testing import assert_frame_equal


@contextmanager
def does_not_raise():
    yield


def get_correct_zip_file_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"correct/zip_files/logs_{participant_id}.zip")


def get_correct_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"correct/folders/logs_{participant_id}")


def get_missing_awakening_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"missing_awakening/logs_{participant_id}")


def get_missing_samples_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"missing_samples/logs_{participant_id}")


def get_corrupt_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"corrupt/logs_{participant_id}")


def get_missing_awakening_path() -> Path:
    return TEST_DATA_PATH.joinpath(f"missing_awakening/logs_AB12C")


def get_missing_samples_path() -> Path:
    return TEST_DATA_PATH.joinpath(f"missing_samples/logs_AB12C")


def awakening_times_correct() -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "date": ["2019-12-07", "2019-12-08"],
            "day_id": [1, 2],
            "timestamp": [
                pd.Timestamp("2019-12-07 07:31:16.418000", tz="Europe/Berlin"),
                pd.Timestamp("2019-12-08 08:46:43.425000", tz="Europe/Berlin"),
            ],
            "awakening_time": ["07:31:16", "08:46:43"],
            "awakening_type": ["self-report", "self-report"],
        }
    )
    data = data.set_index(["date", "day_id"])
    return data


def awakening_times_missing_awakening() -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "date": ["2019-12-07", "2019-12-08"],
            "day_id": [1, 2],
            "timestamp": [
                pd.NaT,
                pd.Timestamp("2019-12-08 08:46:43.425000", tz="Europe/Berlin"),
            ],
            "awakening_time": [np.nan, "08:46:43"],
            "awakening_type": [np.nan, "self-report"],
        }
    )
    data = data.set_index(["date", "day_id"])
    return data


def awakening_times_missing_samples() -> pd.DataFrame:
    return awakening_times_correct()


class TestExampleData:
    def test_get_data_called(self):
        funcs = dict(getmembers(carwatch.example_data, isfunction))
        funcs = {k: v for k, v in funcs.items() if k.startswith("get_")}

        old_get_data = carwatch.example_data._get_data
        with unittest.mock.patch("carwatch.example_data._get_data") as mock:
            for func_name, func in funcs.items():
                mock.side_effect = old_get_data
                if func_name in ["get_carwatch_log_example"]:
                    func("AB12C")
                else:
                    func()
                mock.assert_called()


class TestParticipantLogs:
    @pytest.mark.parametrize(
        "file_name, expected",
        [
            ("test.zip", pytest.raises(FileNotFoundError)),
            ("test.csv", pytest.raises(FileExtensionError)),
            (get_correct_zip_file_path("AB12C"), does_not_raise()),
            (get_correct_folder_path("AB12C"), pytest.raises(FileExtensionError)),
        ],
    )
    def test_from_zip_file_raises(self, file_name, expected):
        with expected:
            file_name = Path(file_name)
            ParticipantLogs.from_zip_file(file_name)

    @pytest.mark.parametrize(
        "file_name",
        [
            (get_correct_zip_file_path("AB12C")),
        ],
    )
    def test_from_zip_file_extract_warning(self, file_name):
        file_name = Path(file_name)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ParticipantLogs.from_zip_file(file_name, extract_folder=True, error_handling="warn")

        with pytest.warns(UserWarning):
            ParticipantLogs.from_zip_file(file_name, extract_folder=True, error_handling="warn")

        self.teardown_method()

    @pytest.mark.parametrize(
        "file_name, extract_folder",
        [
            (get_correct_zip_file_path("AB12C"), True),
            (get_correct_zip_file_path("AB12C"), False),
        ],
    )
    def test_from_zip_file_extract_folder(self, file_name, extract_folder):
        file_name = Path(file_name)
        ParticipantLogs.from_zip_file(file_name, extract_folder=extract_folder)

        folder = file_name.parent.joinpath("logs_AB12C")
        assert folder.exists() == extract_folder, (
            f"Folder should{'' if extract_folder else ' not'} be extracted but it "
            f"does{' not' if extract_folder else ''} exist"
        )
        self.teardown_method()

    @pytest.mark.parametrize(
        "folder_path, expected",
        [
            (get_correct_folder_path("AB12C"), does_not_raise()),
            (get_correct_folder_path("XY89Z"), pytest.raises(FileNotFoundError)),  # does not exist
            (get_correct_folder_path("QR78S"), pytest.raises(FileNotFoundError)),  # empty folder
        ],
    )
    def test_from_folder_raises(self, folder_path, expected):
        with expected:
            folder_path = Path(folder_path)
            ParticipantLogs.from_folder(folder_path)

    @pytest.mark.parametrize(
        "folder_path, error_handling, expected",
        [
            (get_correct_folder_path("AB12C"), "warn", does_not_raise()),
            (get_correct_folder_path("AB12C"), "raise", does_not_raise()),
            (get_corrupt_folder_path("AB12C"), "warn", pytest.warns(UserWarning)),
            (get_corrupt_folder_path("AB12C"), "raise", pytest.raises(LogDataParseError)),
        ],
    )
    def test_parse_log_data_warns_raises(self, folder_path, error_handling, expected):
        with expected:
            ParticipantLogs.from_folder(folder_path, error_handling=error_handling)

    @pytest.mark.parametrize(
        "attribute, expected",
        [
            # study metadata
            ("subject_id", "AB12C"),
            ("study_type", "CAR"),
            ("has_evening_sample", True),
            ("time_points", [0, 15, 30, 45, 60]),
            ("num_saliva_samples", 5),
            ("saliva_ids", {0: "S1", 1: "S2", 2: "S3", 3: "S4", 4: "S5", 5: "SA"}),
            # phone metadata
            ("app_version", "1.1.0"),
            ("android_version", 28),
            ("phone_model", "ONEPLUS A6013"),
            ("phone_manufacturer", "OnePlus"),
            # data
            ("start_date", pd.Timestamp("2019-12-05", tz="Europe/Berlin")),
            ("end_date", pd.Timestamp("2019-12-08", tz="Europe/Berlin")),
            (
                "log_dates",
                [
                    pd.Timestamp(date, tz="Europe/Berlin")
                    for date in ["2019-12-05", "2019-12-06", "2019-12-07", "2019-12-08"]
                ],
            ),
        ],
    )
    def test_parse_log_data(self, attribute, expected):
        folder_path = get_correct_folder_path("AB12C")
        logs = ParticipantLogs.from_folder(folder_path)
        if attribute in ["log_dates"]:
            TestCase().assertListEqual(list(getattr(logs, attribute)), expected)
        else:
            assert getattr(logs, attribute) == expected

    def test_filter_log_data(self):
        folder_path = get_correct_folder_path("AB12C")
        logs = ParticipantLogs.from_folder(folder_path)
        logs_filtered = logs.filter_logs(action="barcode_scanned")
        assert logs_filtered.shape == (13, 2)
        assert len(logs_filtered["action"].unique()) == 1

        logs_filtered = logs.filter_logs(action="hallo")
        assert logs_filtered.shape == (0, 0)

        logs_filtered = logs.filter_logs(date="2019-12-05")
        assert logs_filtered.shape == (3, 2)
        assert len(logs_filtered.index.normalize().unique()) == 1

        logs_filtered = logs.filter_logs(date="2019-12-04")
        assert logs_filtered.shape == (0, 2)

        logs_filtered = logs.filter_logs(date="")
        assert logs_filtered.shape == (83, 2)

    def test_get_extras_for_log_action(self):
        folder_path = get_correct_folder_path("AB12C")
        logs = ParticipantLogs.from_folder(folder_path)
        extras = logs.get_extras_for_log_action(action="barcode_scanned")
        TestCase().assertDictEqual(extras, {"id": 815, "saliva_id": 5, "barcode_value": "0690005"})

    @pytest.mark.parametrize(
        "folder_path, expected_df",
        [
            (get_correct_folder_path("AB12C"), awakening_times_correct()),
            (get_missing_awakening_folder_path("AB12C"), awakening_times_missing_awakening()),
            (get_missing_samples_folder_path("AB12C"), awakening_times_missing_samples()),
        ],
    )
    def test_awakening_times(self, folder_path, expected_df):
        logs = ParticipantLogs.from_folder(folder_path)
        awakening_times = logs.awakening_times()

        assert_frame_equal(expected_df, awakening_times)

    def test_data_as_df_correct(self):
        folder_path = get_correct_folder_path("AB12C")
        logs = ParticipantLogs.from_folder(folder_path)
        df = logs.data_as_df()
        _assert_is_dtype(df, pd.DataFrame)
        _assert_is_dtype(df.index, pd.DatetimeIndex)

        # assert that the index is increasing
        assert df.index.is_monotonic_increasing
        # assert that the datetime index is timezone aware
        assert df.index.tz is not None
        # assert that the datetime index is in UTC
        assert df.index.tz.zone == "Europe/Berlin"

        assert df.shape == (83, 2)
        assert df.index.name == "time"
        assert list(df.columns) == ["action", "extras"]

    @pytest.mark.parametrize(
        "error_handling, expected",
        [
            ("ignore", does_not_raise()),
            ("warn", pytest.warns(UserWarning)),
            ("raise", pytest.raises(LogDataParseError)),
        ],
    )
    def test_data_as_df_timestamp_not_monotonic(self, error_handling, expected):
        folder_path = get_corrupt_folder_path("DE34F")
        with expected:
            ParticipantLogs.from_folder(folder_path, error_handling=error_handling)

    @pytest.fixture(autouse=True)
    def after_test(self):
        yield
        self.teardown_method()

    @staticmethod
    def teardown_method():
        folder = TEST_DATA_PATH.joinpath("correct/zip_files/logs_AB12C")
        if folder.exists():
            shutil.rmtree(folder)
