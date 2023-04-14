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
from carwatch.logs import ParticipantLogs, StudyLogs
from carwatch.utils._datatype_validation_helper import _assert_has_columns, _assert_has_index_levels, _assert_is_dtype
from carwatch.utils.exceptions import FileExtensionError, LogDataParseError

TEST_DATA_PATH = Path(__file__).parent.joinpath("test_data")

from pandas._testing import assert_frame_equal, assert_series_equal


@contextmanager
def does_not_raise():
    yield


def get_correct_folder_path_zip() -> Path:
    return TEST_DATA_PATH.joinpath(f"correct/zip_files")


def get_correct_folder_path_folders() -> Path:
    return TEST_DATA_PATH.joinpath(f"correct/folders")


def get_correct_zip_file_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"correct/zip_files/logs_{participant_id}.zip")


def get_correct_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"correct/folders/logs_{participant_id}")


def get_empty_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"empty/logs_{participant_id}")


def get_missing_awakening_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"missing_awakening/logs_{participant_id}")


def get_missing_samples_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"missing_samples/logs_{participant_id}")


def get_corrupt_folder_path(participant_id: str) -> Path:
    return TEST_DATA_PATH.joinpath(f"corrupt/logs_{participant_id}")


def get_missing_awakening_path() -> Path:
    return TEST_DATA_PATH.joinpath("missing_awakening/logs_AB12C")


def get_missing_samples_path() -> Path:
    return TEST_DATA_PATH.joinpath("missing_samples/logs_AB12C")


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


def export_times_correct(sampling_times: bool, awakening_times: bool, include_evening_sample: bool) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "date": ["2019-12-07", "2019-12-08", "2019-12-09"],
            "day_id": [1, 2, 3],
            "awakening_time": ["07:31:16", "08:46:43", np.nan],
            "awakening_type": ["self-report", "self-report", np.nan],
            "sampling_time_S1": ["07:32:29", "08:47:31", np.nan],
            "sampling_time_S2": ["07:47:50", "09:02:43", np.nan],
            "sampling_time_S3": ["08:03:05", "09:17:53", np.nan],
            "sampling_time_S4": ["08:18:12", "09:32:58", np.nan],
            "sampling_time_S5": ["08:33:19", "09:48:05", np.nan],
            "sampling_time_SA": ["22:53:22", "23:52:43", "22:29:10"],
        }
    )
    data = data.set_index(["date", "day_id"])
    if not sampling_times:
        data = data.drop(
            columns=[col for col in data.columns if col.startswith("sampling_time")], errors="ignore"
        ).dropna(axis=0, how="all")
    if not awakening_times:
        data = data.drop(columns=[col for col in data.columns if col.startswith("awakening")], errors="ignore").dropna(
            axis=0, how="all"
        )
    if not include_evening_sample:
        data = data.drop(columns=["sampling_time_SA"], errors="ignore").dropna(axis=0, how="all")

    return data


def export_times_correct_wide(
    sampling_times: bool, awakening_times: bool, include_evening_sample: bool
) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "date_D1": ["2019-12-07"],
            "awakening_time_D1": ["07:31:16"],
            "awakening_type_D1": ["self-report"],
            "sampling_time_S1_D1": ["07:32:29"],
            "sampling_time_S2_D1": ["07:47:50"],
            "sampling_time_S3_D1": ["08:03:05"],
            "sampling_time_S4_D1": ["08:18:12"],
            "sampling_time_S5_D1": ["08:33:19"],
            "sampling_time_SA_D1": ["22:53:22"],
            "date_D2": ["2019-12-08"],
            "awakening_time_D2": ["08:46:43"],
            "awakening_type_D2": ["self-report"],
            "sampling_time_S1_D2": ["08:47:31"],
            "sampling_time_S2_D2": ["09:02:43"],
            "sampling_time_S3_D2": ["09:17:53"],
            "sampling_time_S4_D2": ["09:32:58"],
            "sampling_time_S5_D2": ["09:48:05"],
            "sampling_time_SA_D2": ["23:52:43"],
            "date_D3": ["2019-12-09"],
            "awakening_time_D3": [np.nan],
            "awakening_type_D3": [np.nan],
            "sampling_time_S1_D3": [np.nan],
            "sampling_time_S2_D3": [np.nan],
            "sampling_time_S3_D3": [np.nan],
            "sampling_time_S4_D3": [np.nan],
            "sampling_time_S5_D3": [np.nan],
            "sampling_time_SA_D3": ["22:29:10"],
        },
        index=pd.Index(["AB12C"], name="subject"),
    )
    data = data.stack(dropna=False).unstack()  # so that all dtypes are object (otherwise, np.nan is converted to float)
    if not sampling_times:
        data = data.drop(columns=[col for col in data.columns if col.startswith("sampling_time")], errors="ignore")
    if not awakening_times:
        data = data.drop(columns=[col for col in data.columns if col.startswith("awakening")], errors="ignore")
    if not include_evening_sample:
        data = data.drop(columns=[col for col in data.columns if "SA" in col], errors="ignore")

    if not sampling_times or not include_evening_sample:
        # D3 has no samplings in the morning (only evening), so it should be dropped either if no sampling times
        # should be exported or if no evening sample should be exported
        data = data.drop(columns=data.filter(like="D3").columns)
    return data


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
        ("file_name", "expected"),
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
        ("file_name", "extract_folder"),
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
        ("folder_path", "expected"),
        [
            (get_correct_folder_path("AB12C"), does_not_raise()),
            (get_correct_folder_path("XY89Z"), pytest.raises(FileNotFoundError)),  # does not exist
            (get_empty_folder_path("QR78S"), pytest.raises(FileNotFoundError)),  # empty folder
        ],
    )
    def test_from_folder_raises(self, folder_path, expected):
        with expected:
            folder_path = Path(folder_path)
            ParticipantLogs.from_folder(folder_path)

    @pytest.mark.parametrize(
        ("folder_path", "error_handling", "expected"),
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
        ("attribute", "expected"),
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
        ("folder_path", "expected_df"),
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
        _assert_has_columns(df, [["action", "extras"]])

    @pytest.mark.parametrize(
        ("error_handling", "expected"),
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

    @pytest.mark.parametrize(
        "file_path",
        [
            (get_correct_zip_file_path("AB12C")),
        ],
    )
    def test_split_sampling_days_df(self, file_path):
        log_data = ParticipantLogs.from_zip_file(file_path)
        data = log_data.split_sampling_days()
        _assert_is_dtype(data, pd.DataFrame)
        _assert_is_dtype(data.index, pd.MultiIndex)
        _assert_has_index_levels(data, ["date", "time"])

    @pytest.mark.parametrize(
        "file_path",
        [
            (get_correct_zip_file_path("AB12C")),
        ],
    )
    def test_split_sampling_days_dict(self, file_path):
        log_data = ParticipantLogs.from_zip_file(file_path)
        data = log_data.split_sampling_days(return_dict=True)
        _assert_is_dtype(data, dict)
        assert len(data) == 4

    def test_split_sampling_days_split_into_nights(self):
        file_path = get_correct_zip_file_path("AB12C")
        log_data = ParticipantLogs.from_zip_file(file_path)
        data = log_data.split_sampling_days(split_into_nights=True, return_dict=True)
        _assert_is_dtype(data, dict)
        assert len(data) == 4
        TestCase().assertListEqual(list(data.keys()), ["2019-12-05", "2019-12-07", "2019-12-08", "2019-12-09"])
        TestCase().assertListEqual([len(x) for x in data.values()], [3, 40, 36, 4])
        TestCase().assertListEqual(
            [x.index[0].normalize() == x.index[-1].normalize() for x in data.values()],
            [
                True,
                False,
                False,
                True,
            ],  # 2019-12-07 and 2019-12-08 contain cortisol data with evening samples, i.e., on two days
        )

    def test_split_sampling_days_split_into_days(self):
        file_path = get_correct_zip_file_path("AB12C")
        log_data = ParticipantLogs.from_zip_file(file_path)
        data = log_data.split_sampling_days(split_into_nights=False, return_dict=True)
        _assert_is_dtype(data, dict)
        assert len(data) == 4
        TestCase().assertListEqual(list(data.keys()), ["2019-12-05", "2019-12-06", "2019-12-07", "2019-12-08"])
        TestCase().assertListEqual([len(x) for x in data.values()], [3, 10, 37, 33])
        TestCase().assertListEqual(
            [x.index[0].normalize() == x.index[-1].normalize() for x in data.values()],
            [True, True, True, True],  # correctly split into days
        )

    @pytest.mark.parametrize(
        ("include_evening_sample", "expected"),
        [
            (
                True,
                {
                    "shape": (13, 2),
                    "date": ["2019-12-07", "2019-12-08", "2019-12-09"],
                    "saliva_type": ["evening", "morning"],
                    "saliva_id": ["S1", "S2", "S3", "S4", "S5", "SA"],
                    "day_id": [1, 2, 3],
                    "index_levels": ["date", "saliva_type", "saliva_id", "day_id"],
                    "sampling_time": [
                        "22:53:22",
                        "07:32:29",
                        "07:47:50",
                        "08:03:05",
                        "08:18:12",
                        "08:33:19",
                        "23:52:43",
                        "08:47:31",
                        "09:02:43",
                        "09:17:53",
                        "09:32:58",
                        "09:48:05",
                        "22:29:10",
                    ],
                },
            ),
            (
                False,
                {
                    "shape": (10, 2),
                    "date": ["2019-12-07", "2019-12-08"],
                    "saliva_type": ["morning"],
                    "saliva_id": ["S1", "S2", "S3", "S4", "S5"],
                    "day_id": [1, 2],
                    "index_levels": ["date", "saliva_type", "saliva_id", "day_id"],
                    "sampling_time": [
                        "07:32:29",
                        "07:47:50",
                        "08:03:05",
                        "08:18:12",
                        "08:33:19",
                        "08:47:31",
                        "09:02:43",
                        "09:17:53",
                        "09:32:58",
                        "09:48:05",
                    ],
                },
            ),
        ],
    )
    def test_sampling_times_correct(self, include_evening_sample, expected):
        file_path = get_correct_zip_file_path("AB12C")
        log_data = ParticipantLogs.from_zip_file(file_path)
        sampling_times = log_data.sampling_times(include_evening_sample=include_evening_sample)

        _assert_is_dtype(sampling_times, pd.DataFrame)
        _assert_has_columns(sampling_times, [["timestamp", "sampling_time"]])
        assert sampling_times.shape == expected["shape"]
        _assert_has_index_levels(sampling_times, expected["index_levels"])
        for index_name in ["date", "saliva_type", "saliva_id", "day_id"]:
            TestCase().assertListEqual(
                sorted(sampling_times.index.get_level_values(index_name).unique()), expected[index_name]
            )
        TestCase().assertListEqual(list(sampling_times["sampling_time"]), expected["sampling_time"])

    @pytest.mark.parametrize(
        ("include_evening_sample", "expected"),
        [
            (
                True,
                {
                    "shape": (11, 2),
                    "date": ["2019-12-07", "2019-12-08", "2019-12-09"],
                    "saliva_type": ["evening", "morning"],
                    "saliva_id": ["S1", "S2", "S3", "S4", "S5", "SA"],
                    "day_id": [1, 2, 3],
                    "index_levels": ["date", "saliva_type", "saliva_id", "day_id"],
                    "sampling_time": [
                        "07:32:29",
                        "07:47:50",
                        "08:18:12",
                        "08:33:19",
                        "23:52:43",
                        "08:47:31",
                        "09:02:43",
                        "09:17:53",
                        "09:32:58",
                        "09:48:05",
                        "22:29:10",
                    ],
                },
            ),
            (
                False,
                {
                    "shape": (9, 2),
                    "date": ["2019-12-07", "2019-12-08"],
                    "saliva_type": ["morning"],
                    "saliva_id": ["S1", "S2", "S3", "S4", "S5"],
                    "day_id": [1, 2],
                    "index_levels": ["date", "saliva_type", "saliva_id", "day_id"],
                    "sampling_time": [
                        "07:32:29",
                        "07:47:50",
                        "08:18:12",
                        "08:33:19",
                        "08:47:31",
                        "09:02:43",
                        "09:17:53",
                        "09:32:58",
                        "09:48:05",
                    ],
                },
            ),
        ],
    )
    def test_sampling_times_missing_samples(self, include_evening_sample, expected):
        folder_path = get_missing_samples_folder_path("AB12C")
        log_data = ParticipantLogs.from_folder(folder_path)
        sampling_times = log_data.sampling_times(include_evening_sample=include_evening_sample)

        _assert_is_dtype(sampling_times, pd.DataFrame)
        _assert_has_columns(sampling_times, [["timestamp", "sampling_time"]])
        assert sampling_times.shape == expected["shape"]
        _assert_has_index_levels(sampling_times, expected["index_levels"])
        for index_name in ["date", "saliva_type", "saliva_id", "day_id"]:
            TestCase().assertListEqual(
                sorted(sampling_times.index.get_level_values(index_name).unique()), expected[index_name]
            )
        TestCase().assertListEqual(list(sampling_times["sampling_time"]), expected["sampling_time"])

    @pytest.mark.parametrize(
        ("sampling_times", "awakening_times", "include_evening_sample", "expected"),
        [
            (True, True, True, does_not_raise()),
            (True, True, False, does_not_raise()),
            (True, False, True, does_not_raise()),
            (True, False, False, does_not_raise()),
            (False, True, True, does_not_raise()),
            (False, True, False, does_not_raise()),
            (False, False, True, pytest.raises(ValueError)),
            (False, False, False, pytest.raises(ValueError)),
        ],
    )
    def test_export_times_raises(self, sampling_times, awakening_times, include_evening_sample, expected):
        log_data = ParticipantLogs.from_zip_file(get_correct_zip_file_path("AB12C"))
        with expected:
            log_data.export_times(
                sampling_times=sampling_times,
                awakening_times=awakening_times,
                include_evening_sample=include_evening_sample,
            )

    @pytest.mark.parametrize(
        ("sampling_times", "awakening_times", "include_evening_sample"),
        [
            (True, True, True),
            (True, True, False),
            (True, False, True),
            (True, False, False),
            (False, True, True),
            (False, True, False),
        ],
    )
    def test_export_times(self, sampling_times, awakening_times, include_evening_sample):
        expected = export_times_correct(sampling_times, awakening_times, include_evening_sample)

        log_data = ParticipantLogs.from_zip_file(get_correct_zip_file_path("AB12C"))
        out = log_data.export_times(
            sampling_times=sampling_times,
            awakening_times=awakening_times,
            include_evening_sample=include_evening_sample,
        )
        assert_frame_equal(out, expected)

    @pytest.mark.parametrize(
        ("sampling_times", "awakening_times", "include_evening_sample"),
        [
            (True, True, True),
            (True, True, False),
            (True, False, True),
            (True, False, False),
            (False, True, True),
            (False, True, False),
        ],
    )
    def test_export_times_wide(self, sampling_times, awakening_times, include_evening_sample):
        expected = export_times_correct_wide(sampling_times, awakening_times, include_evening_sample)

        log_data = ParticipantLogs.from_zip_file(get_correct_zip_file_path("AB12C"))
        out = log_data.export_times(
            sampling_times=sampling_times,
            awakening_times=awakening_times,
            include_evening_sample=include_evening_sample,
            wide_format=True,
        )

        assert_frame_equal(out, expected)

    @pytest.fixture(autouse=True)
    def after_test(self):
        yield
        self.teardown_method()

    @staticmethod
    def teardown_method():
        folder = TEST_DATA_PATH.joinpath("correct/zip_files/logs_AB12C")
        if folder.exists():
            shutil.rmtree(folder)


class TestStudyLogs:
    @pytest.mark.parametrize(
        ("folder_path", "expected"),
        [
            (TEST_DATA_PATH, pytest.raises(FileNotFoundError)),
            (Path("."), pytest.raises(FileNotFoundError)),
            (get_correct_folder_path_zip(), does_not_raise()),
            (get_correct_folder_path_folders(), does_not_raise()),
            (
                get_empty_folder_path("logs_QR78S").parent,
                pytest.raises(FileNotFoundError),
            ),  # parent folder should contain folder for logs_QR78S, which are emtpy and thus raise an error
            (
                get_empty_folder_path("logs_QR78S"),
                pytest.raises(FileNotFoundError),
            ),  # folder is empty and thus raises an error
        ],
    )
    def test_from_folder_raises(self, folder_path, expected):
        with expected:
            StudyLogs.from_folder(folder_path)

    @pytest.mark.parametrize(
        ("expected", "name"),
        [
            (pd.Series({"AB12C": 28, "DE34F": 28, "GH56I": 26}), "android_version"),
            (pd.Series({"AB12C": "1.1.0", "DE34F": "1.1.0", "GH56I": "1.1.0"}), "app_version"),
            (pd.Series({"AB12C": "ONEPLUS A6013", "DE34F": "ONEPLUS A6013", "GH56I": "SM-G930F"}), "phone_model"),
            (pd.Series({"AB12C": "OnePlus", "DE34F": "OnePlus", "GH56I": "samsung"}), "phone_manufacturer"),
        ],
    )
    def test_attributes(self, expected, name):
        study_logs = StudyLogs.from_folder(get_correct_folder_path_zip())
        participants = ["AB12C", "DE34F", "GH56I"]
        assert isinstance(study_logs, StudyLogs)
        assert len(study_logs) == 3
        assert len(study_logs.participants) == 3
        TestCase().assertListEqual(sorted(study_logs.participants), participants)
        for key in study_logs:
            assert key in participants
            assert isinstance(study_logs[key], ParticipantLogs)

        expected = expected.to_frame(name)
        expected.index.name = "subject"
        assert_frame_equal(getattr(study_logs, f"{name}s"), expected)

    def test_data_as_df(self):
        study_logs = StudyLogs.from_folder(get_correct_folder_path_zip())
        out = study_logs.data_as_df()
        for key in study_logs:
            logs = get_correct_zip_file_path(key)
            expected = ParticipantLogs.from_zip_file(logs).data_as_df()

            assert_frame_equal(out.xs(key, level="subject"), expected)

    @pytest.fixture(autouse=True)
    def after_test(self):
        yield
        self.teardown_method()

    @staticmethod
    def teardown_method():
        for subject in ["AB12C", "DE34F", "GH56J"]:
            folder = TEST_DATA_PATH.joinpath(f"correct/zip_files/logs_{subject}")
            if folder.exists():
                shutil.rmtree(folder)
