"""Log files from one single participant."""
import json
import warnings
import zipfile
from pathlib import Path
from typing import IO, Any, Dict, Literal, Optional, Sequence, Union

import numpy as np
import pandas as pd

from carwatch.utils._datatype_validation_helper import _assert_file_extension, _assert_is_dtype
from carwatch.utils._types import path_t, str_t
from carwatch.utils.exceptions import LogDataInvalidError


class ParticipantLogs:
    """Class representing log data from one single participant."""

    log_actions: Dict[str, Sequence[str]] = {
        "app_metadata": ["app_version_code", "app_version_name"],
        "phone_metadata": [
            "brand",
            "manufacturer",
            "model",
            "version_sdk_level",
            "version_security_patch",
            "version_release",
        ],
        "subject_id_set": ["subject_id", "subject_condition"],
        "alarm_set": ["alarm_id", "timestamp", "is_repeating", "is_hidden", "hidden_timestamp"],
        "timer_set": ["alarm_id", "timestamp"],
        "alarm_cancel": ["alarm_id"],
        "alarm_ring": ["alarm_id", "saliva_id"],
        "alarm_snooze": ["alarm_id", "snooze_duration", "source"],
        "alarm_stop": ["alarm_id", "source", "saliva_id"],
        "alarm_killall": [],
        "evening_salivette": ["alarm_id"],
        "barcode_scan_init": [],
        "barcode_scanned": ["alarm_id", "saliva_id", "barcode_value"],
        "invalid_barcode_scanned": ["barcode_value"],
        "duplicate_barcode_scanned": ["barcode_value", "other_barcodes"],
        "spontaneous_awakening": ["alarm_id"],
        "lights_out": [],
        "day_finished": ["day_counter"],
        "service_started": [],
        "service_stopped": [],
        "screen_off": [],
        "screen_on": [],
        "user_present": [],
        "phone_boot_init": [],
        "phone_boot_complete": [],
    }

    def __init__(self, data: pd.DataFrame, tz: str, error_handling: str = "ignore") -> None:
        """Initialize new ``ParticipantLogs`` instance.

        .. note::
            Usually you shouldn't use this init directly.
            Use the provided `from_zip_file` or `from_folder` constructors to load CARWatch log data.

        Parameters
        ----------
        data : :class:`~pandas.DataFrame`
            log data as dataframe
        tz : str

        """
        self._data: pd.DataFrame = data
        self.tz: str = tz
        self.subject_id: str
        self.error_handling: str = error_handling
        self.log_dates: Optional[Sequence[pd.Timestamp]] = None
        self.app_metadata: Optional[Dict[str, Any]] = None
        self.phone_metadata: Optional[Dict[str, Any]] = None
        self._extract_info()

    @classmethod
    def from_zip_file(
        cls,
        path: path_t,
        extract_folder: Optional[bool] = False,
        overwrite_unzipped_logs: Optional[bool] = False,
        tz: Optional[str] = "Europe/Berlin",
        error_handling: Optional[Literal["ignore", "warn", "raise"]] = "ignore",
    ) -> "ParticipantLogs":
        """Load log files from one subject.

        Parameters
        ----------
        path : :class:`~pathlib.Path` or str
            path to zip file from one participant
        extract_folder : bool, optional
            ``True`` to extract zip file to a folder with the same name as the zip file,
            ``False`` to only read content and not extract. Default: ``False``
        overwrite_unzipped_logs : bool, optional
            ``True`` to overwrite already unzipped log files, ``False`` to not overwrite.
            Only relevant if ``extract_folder`` is ``True``. Default: ``False``
        error_handling : {"ignore", "warn", "raise"}, optional
            how to handle error when parse log data. ``error_handling`` can be one of the following:

            * "ignore" to ignore warning.
            * "warn" to issue warning when no "Subject ID Set" action was found in the data (indicating that a
              participant did not correctly register itself for the study or that log data is corrupted)
            * "raise" to raise an exception when no "Subject ID Set" action was found in the data.
            Default: "ignore"
        tz : str, optional
            timezone of the log data. Default: "Europe/Berlin"

        Returns
        -------
        :class:`~carwatch.logs.ParticipantLogs`
            log data from one participant

        """
        path = Path(path)

        _assert_file_extension(path, ".zip")
        with zipfile.ZipFile(path, "r") as zip_ref:
            if extract_folder:
                # extract zip file to folder with same name as zip file
                export_folder = path.parent.joinpath(path.stem)
                export_folder.mkdir(exist_ok=True)
                if overwrite_unzipped_logs or len(list(export_folder.glob("*"))) == 0:
                    zip_ref.extractall(export_folder)
                else:
                    # folder not empty => inform user and load folder
                    warnings.warn(
                        f"Folder {export_folder.name} already contains log files which will be loaded. "
                        f"Set `overwrite_logs_unzip = True` to overwrite log files."
                    )
                log_data = cls._folder_to_dataframe(export_folder, tz)
            else:
                log_data = cls._zip_file_to_dataframe(zip_ref, tz)

        return cls(log_data, tz, error_handling)

    @classmethod
    def from_folder(
        cls,
        folder_path: path_t,
        tz: Optional[str] = "Europe/Berlin",
        error_handling: Optional[Literal["ignore", "warn", "raise"]] = "ignore",
    ) -> "ParticipantLogs":
        """Load log files from one participant.

        Parameters
        ----------
        folder_path : :class:`~pathlib.Path` or str
            path to folder containing log files from one participant
        tz : str
            timezone of the log data
        error_handling : {"ignore", "warn", "raise"}, optional
            how to handle error when parsing log data. ``error_handling`` can be one of the following:

            * "ignore" to ignore warning.
            * "warn" to issue warning when no "Subject ID Set" action was found in the data (indicating that a
                participant did not correctly register itself for the study or that log data is corrupted)
            * "raise" to raise an exception when no "Subject ID Set" action was found in the data.
            Default: "ignore"


        Returns
        -------
        :class:`~carwatch.logs.ParticipantLogs`
            log data from one participant

        """
        folder_path = Path(folder_path)
        log_data = cls._folder_to_dataframe(folder_path, tz)
        return cls(log_data, tz, error_handling=error_handling)

    @classmethod
    def _folder_to_dataframe(cls, folder_path: Path, tz: str) -> pd.DataFrame:
        """Load log data from folder of one participant and return it as dataframe.

        Parameters
        ----------
        folder_path : :class:`~pathlib.Path` or str
            path to folder containing log files from participant
        tz : str
            timezone of the log data

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with log data for one participant

        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder {folder_path} does not exist.")
        file_list = sorted(folder_path.glob("*.csv"))
        if len(file_list) == 0:
            raise FileNotFoundError(f"No log files found in folder {folder_path}.")
        return pd.concat([cls._load_log_file_csv(file, tz) for file in file_list])

    @classmethod
    def _zip_file_to_dataframe(cls, zip_ref: zipfile.ZipFile, tz: str) -> pd.DataFrame:
        """Load log data from zip file of one participant and return it as dataframe.

        Parameters
        ----------
        zip_ref : :class:`~zipfile.ZipFile`
            zip file containing log files from participant
        tz : str
            timezone of the log data

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with log data for one participant

        """
        file_list = [
            f
            for f in zip_ref.filelist
            if f.filename.endswith(".csv")
            and not f.filename.startswith(".")  # ignore hidden files
            and not f.filename.startswith("__")  # ignore hidden files
        ]
        return pd.concat([cls._load_log_file_csv(zip_ref.open(file), tz) for file in file_list])

    @classmethod
    def _load_log_file_csv(
        cls,
        file_path: Union[Path, IO[bytes]],
        tz: str,
    ) -> pd.DataFrame:
        df = pd.read_csv(file_path, sep=";", header=None, names=["time", "action", "extras"])

        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df = df.set_index("time")
        df.index = df.index.tz_localize("UTC").tz_convert(tz)
        df = df.sort_index()
        df = df.apply(cls._parse_date, args=(tz,), axis=1)
        return df

    @classmethod
    def _parse_date(cls, row: pd.Series, tz: str) -> pd.Series:
        """Parse date in "timestamp" and "timestamp_hidden" columns of a pandas series.

        Parameters
        ----------
        row : :class:`~pandas.Series`
            one row of a dataframe
        tz : str
            timezone of the log data

        Returns
        -------
        :class:`~pandas.Series`
            series with parsed date

        """
        json_extra = json.loads(row["extras"])
        row_cpy = row.copy()
        keys = ["timestamp", "timestamp_hidden"]
        for key in keys:
            if key in json_extra:
                # convert to datetime and localize
                time = pd.to_datetime(json_extra[key], unit="ms")
                time = time.tz_localize("UTC").tz_convert(tz)
                json_extra[key] = str(time)

        # fix wrong key for saliva_id in "alarm_ring" action (old app versions)
        if "extra_saliva_id" in json_extra:
            json_extra["saliva_id"] = json_extra["extra_saliva_id"]
            del json_extra["extra_saliva_id"]
        row_cpy["extras"] = json.dumps(json_extra)
        return row_cpy

    def _extract_info(self) -> None:
        """Extract log data information."""
        # Subject Information
        subject_dict = self.get_extras_for_log_action("subject_id_set")
        try:
            self.subject_id = subject_dict["subject_id"]
        except KeyError:
            if self.error_handling == "warn":
                warnings.warn("Action 'Subject ID Set' not found - Log Data may be invalid!")
            elif self.error_handling == "raise":
                raise LogDataInvalidError("Action 'Subject ID Set' not found - Log Data may be invalid!")
        # App Metadata
        self.app_metadata = self.get_extras_for_log_action("app_metadata")
        # Phone Metadata
        self.phone_metadata = self.get_extras_for_log_action("phone_metadata")

        # Log Info
        self.log_dates = np.array(list(self._data.index.normalize().unique()))

    #
    #     def _ipython_display_(self):
    #         self.print_info()
    #
    #     def print_info(self):
    #         """Display Markdown-formatted log data information."""
    #         try:
    #             from IPython.core.display import Markdown, display  # pylint:disable=import-outside-toplevel
    #         except ImportError as e:
    #             raise ImportError(
    #                 "Displaying LogData information failed because "
    #                 "IPython cannot be imported. Install it via 'pip install ipython'."
    #             ) from e
    #
    #         display(Markdown("Subject ID: **{}**".format(self.subject_id)))
    #         display(Markdown("Condition: **{}**".format(self.condition)))
    #         display(Markdown("App Version: **{}**".format(self.app_version)))
    #         display(Markdown("Android Version: **{}**".format(self.android_version)))
    #         display(Markdown("Phone: **{}**".format(self.model)))
    #         display(Markdown("Logging Days: **{} - {}**".format(str(self.start_date), str(self.end_date))))
    #

    @property
    def android_version(self) -> int:
        """Return the Android version.

        Returns
        -------
        int
            SDK version of Android version or 0 if information is not available

        """
        return self.phone_metadata.get("version_sdk_level", 0)

    @property
    def app_version(self) -> str:
        """Return the CARWatch App version.

        Returns
        -------
        str
            CARWatch App version

        """
        return self.app_metadata.get("version_name").split("_")[0]

    @property
    def phone_manufacturer(self) -> str:
        """Return the phone manufacturer.

        Returns
        -------
        str
            name of the phone manufacturer or "n/a" if information is not available

        """
        return self.phone_metadata.get("manufacturer", "n/a")

    @property
    def phone_model(self) -> str:
        """Return the phone model.

        Returns
        -------
        str
            name of the phone model or "n/a" if information is not available

        """
        return self.phone_metadata.get("model", "n/a")

    @property
    def start_date(self) -> pd.Timestamp:
        """Return the start date of log data, i.e., the first day with log data.

        ..note:: This is most likely the day the app was installed and configured and not necessarily the date
        when the CAR procedure was started.

        Returns
        -------
        :class:`~pandas.Timestamp`
            start date


        """
        if self.log_dates is not None and len(self.log_dates) > 0:
            return self.log_dates[0]
        return pd.Timestamp()

    @property
    def end_date(self) -> pd.Timestamp:
        """Return end date of log data.

        ..note:: This is not necessarily the date when the CAR procedure was finished.

        Returns
        -------
        :class:`~pandas.Timestamp`
            start date

        """
        if self.log_dates is not None and len(self.log_dates) > 0:
            return self.log_dates[-1]
        return pd.Timestamp()

    @property
    def num_saliva_samples(self) -> int:
        """Return number of saliva samples.

        Returns
        -------
        int
            number of saliva samples

        """
        # TODO change when new app version is released
        return 5

    @property
    def sampling_time_differences(self) -> Sequence[int]:
        """Return times between saliva samples.

        Returns
        -------
        list of int
            times between saliva samples in minutes

        """
        # TODO change when new app version is released
        return [15] * (self.num_saliva_samples - 1)

    def data_as_df(self) -> pd.DataFrame:
        """Return log data as dataframe.

        Returns
        -------
        :class:`~pandas.DataFrame`
            log data

        """
        return self._data.copy()

    def filter_logs(
        self,
        *,
        data: Optional[pd.DataFrame] = None,
        action: Optional[str_t] = None,
        date: Optional[Union[pd.Timestamp, str]] = None,
    ) -> pd.DataFrame:
        """Filter logs by action and date.

        Parameters
        ----------
        data : :class:`~pandas.DataFrame`, optional
            dataframe with log data to filter or ``None`` to use the log data of the current instance. Default: ``None``
        action : str or list of str, optional
            action(s) to filter log data for or ``None`` to filter for all actions. Default: ``None``
        date : :class:`~pandas.Timestamp` or str, optional
            date to filter log data for or ``None`` to filter for all dates. Default: ``None``

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with filtered log data

        """
        return self._get_logs_for_action(data=data, action=action, date=date)

    def _get_logs_for_date(self, data: pd.DataFrame, date: Union[str, pd.Timestamp]) -> pd.DataFrame:
        """Filter log data for a specific date.

        Parameters
        ----------
        data : :class:`~pandas.DataFrame`
            dataframe with log data to filter
        date : str or :class:`~pandas.Timestamp`
            date to filter log data for

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with log data for specific date

        """
        date = pd.Timestamp(date).tz_localize(self.tz)

        if date is pd.NaT:
            return data

        return data.loc[data.index.normalize() == date]

    def split_sampling_days(
        self, split_night: Optional[bool] = True, return_dict: Optional[bool] = False
    ) -> Dict[str, pd.DataFrame]:
        """Split continuous log data into individual sampling days.

        This function splits data into individual sampling days.
        The split is performed at 6pm because that's the time of day when the probability of
        sleeping is the lowest.

        Parameters
        ----------
        split_night : bool, optional
            If ``True``, split data into *nights*, assuming that samples taken in the evening correspond to the
            next day. This means that data are split at 6pm. This is the typical way if cortisol awakening response
            (CAR) data with preceding evening saliva samples are assessed.
            If ``False``, split data into *days*, assuming that all samples taken at one day belong to the same day.
            This is the typical way if cortisol daily profiles with cortisol samples over the whole day are assessed.
            Default: ``True``
        return_dict : bool, optional
            If ``True``, return a dictionary with sampling date (keys) and log dataframes (values). If ``False``,
            a concatenated dataframe is returned. Default: ``False``


        Returns
        -------
        dict
            dictionary with sampling date (keys) and log dataframes (values).

        """
        data = self.data_as_df()
        _assert_is_dtype(data.index, pd.DatetimeIndex)
        # split data per day
        date_diff = np.diff(data.index.date)
        date_diff = np.append(date_diff[0], date_diff)
        idx_date = np.where(date_diff)[0]

        dict_data = self._split_night(data, idx_date) if split_night else self._split_day(data, idx_date)

        if return_dict:
            return dict_data

        return pd.concat(dict_data, names=["date"])

    @staticmethod
    def _split_night(data: pd.DataFrame, idx_date: np.ndarray) -> Dict[str, pd.DataFrame]:
        # split data per time: split at 6 pm, because that's the time of day
        # when the probability of sleeping is the lowest
        time_6pm = pd.Timestamp("18:00:00").time()

        time_diff = data.index.time <= time_6pm
        time_diff = np.append(time_diff[0], time_diff)
        idx_time = np.where(np.diff(time_diff))[0]

        # concatenate both splitting criteria and split data
        idx_split = np.unique(np.concatenate([idx_date, idx_time]))
        data_split = np.split(data, idx_split)

        # concatenate data from one night (data between 6 pm and 12 am from the previous day and
        # between 12 am and 6 pm of the next day)
        for i, df in enumerate(data_split):
            if i < (len(data_split) - 1):
                df_curr = df
                df_next = data_split[i + 1]

                date_curr = df_curr.index[0].date()
                date_next = df_next.index[0].date()
                time_curr = df_curr.index[0].time()
                time_next = df_next.index[0].time()

                # check if dates are consecutive and if first part is after 6 pm and second part is before 6 am
                if (date_next == date_curr + pd.Timedelta("1d")) and (time_curr > time_6pm > time_next):
                    data_split[i] = pd.concat([df_curr, df_next])
                    # delete the second part
                    del data_split[i + 1]

        # create dict with data from each night. dictionary keys are the dates.
        dict_data = {}
        for df in data_split:
            date = df.index[-1].normalize().date()
            # By convention, if the recording started after 6 pm the date is assumed to be corresponding
            # to the next morning
            if df.index[-1].time() > time_6pm:
                date += pd.Timedelta("1d")
            dict_data[str(date)] = df

        return dict_data

    @staticmethod
    def _split_day(data, idx_date):
        data_split = np.split(data, idx_date)
        dict_data = {}
        for df in data_split:
            date = df.index[0].normalize().date()
            dict_data[str(date)] = df

        return dict_data

    def _get_logs_for_action(
        self,
        *,
        data: Optional[pd.DataFrame] = None,
        action: Optional[str_t] = None,
        date: Optional[Union[pd.Timestamp, str]] = None,
        rows: Optional[Union[str, int, Sequence[int]]] = None,
    ) -> Union[pd.DataFrame, pd.Series]:
        """Filter log data for a specific action.

        Parameters
        ----------
        data : :class:`~pandas.DataFrame`, optional
            dataframe with log data to filter or ``None`` to use the log data of the current instance. Default: ``None``
        action : str or list of str, optional
            action(s) to filter log data for or ``None`` to filter for all actions. Default: ``None``
        date : :class:`~pandas.Timestamp` or str, optional
            filter log data to only contain data from one selected date or ``None`` to include data from all dates.
            Default: ``None``
        rows : str, int, or list of int, optional
            index label (or list of such) to slice filtered log data (e.g., only select the first action) or
            ``None`` to include all data. Default: ``None``

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with log data for specific action

        """
        if data is None:
            data = self.data_as_df()

        if date is not None:
            data = self._get_logs_for_date(data=data, date=date)

        if isinstance(action, str):
            action = [action]
        if action is None:
            return data
        if all(a not in self.log_actions.keys() for a in action):
            return pd.DataFrame()

        data = data.set_index("action", append=True)
        data_filter = data.reindex(action, level="action").reset_index(level="action")
        if rows:
            data_filter = data_filter.iloc[rows, :]
        return data_filter

    def get_extras_for_log_action(self, action: str) -> Dict[str, str]:
        """Extract log data extras from log data.

        Parameters
        ----------
        action : :class:`datetime.date` or str
            action to filter log data

        Returns
        -------
        dict
            dictionary with log extras for specific action

        """
        row = self._get_logs_for_action(action=action, rows=0)
        if row.empty:
            return {}

        return json.loads(row["extras"].iloc[0])

    def sampling_times(
        self,
        include_evening_sample: Optional[bool] = True,
        add_day_id: Optional[bool] = True,
    ) -> pd.DataFrame:
        """Get sampling times.

        Parameters
        ----------
        include_evening_sample : bool, optional
            ``True`` to include evening sampling times, ``False`` to only include morning sampling times.
            Default: ``True``
        add_day_id : bool, optional
            ``True`` to add an index level with an increasing day id. Default: ``True``

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with sampling times

        """
        data_split = {}
        for day, data in self.split_sampling_days(return_dict=True).items():
            data = self.filter_logs(data=data, action=["barcode_scanned"])
            if len(data) == 0:
                continue
            # expand extras, which is a json string
            extras = data["extras"].apply(json.loads)
            # convert extras to dataframe
            df = pd.DataFrame(list(extras.values))
            df = df[["saliva_id"]]
            # add new columns
            df = df.assign(
                **{"timestamp": data.index, "sampling_time": data.index.strftime("%H:%M:%S"), "saliva_type": "morning"}
            )
            # assign morning or evening "saliva_type" to each saliva_id
            df.loc[df["saliva_id"] >= self.num_saliva_samples, "saliva_type"] = "evening"
            # find the last barcode_scanned event for each saliva_id
            df = df.groupby("saliva_id", sort=False).last()
            df = df.reset_index().set_index(["saliva_type", "saliva_id"])
            # TODO: replace saliva IDs with prefix when supported by app
            data_split[day] = df

        data_concat = pd.concat(data_split, names=["date"])

        if not include_evening_sample:
            data_concat = data_concat.drop("evening", level="saliva_type")

        if add_day_id:
            # assign a unique id to each night, starting with 1
            date_vals = data_concat.index.get_level_values("date")
            data_concat = data_concat.assign(**{"day_id": date_vals.unique().searchsorted(date_vals) + 1})
            data_concat = data_concat.set_index("day_id", append=True)
        return data_concat

    def awakening_times(self, add_day_id: Optional[bool] = True) -> pd.DataFrame:
        """Extract awakening times from log data.

        Parameters
        ----------
        add_day_id : bool, optional
            ``True`` to add an index level with an increasing day id. Default: ``True``

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with awakening times

        """
        data_split = {}
        for day, data in self.split_sampling_days(return_dict=True).items():
            data_action = []
            for log_action in ["spontaneous_awakening", "alarm_stop"]:
                data_filter = self.filter_logs(data=data, action=log_action)
                if len(data_filter) == 0:
                    continue
                # expand extras, which is a json string
                extras = data_filter["extras"].apply(json.loads)
                # convert extras to dataframe
                df = pd.DataFrame(list(extras.values))
                df.index = data_filter.index
                df = data_filter.drop(columns=["extras"]).join(df)
                df = df.assign(**{"awakening_time": data_filter.index.strftime("%H:%M:%S")})
                df = df.set_index("action", append=True)
                data_action.append(df)

            if len(data_action) == 0:
                continue
            data_day = pd.concat(data_action)
            data_day = data_day.iloc[[0], :]
            data_day = data_day.reset_index("action")
            data_day = data_day.rename(columns={"action": "awakening_type"})
            data_day["awakening_type"] = data_day["awakening_type"].replace(
                {"spontaneous_awakening": "self-report", "alarm_stop": "alarm"}
            )
            data_day.index.name = "timestamp"

            # todo test
            if data_day.iloc[0]["awakening_type"] == "alarm" and data_day["saliva_id"].iloc[0] not in [np.nan, 0]:
                data_day["awakening_time"] = np.nan
            data_day = data_day[["awakening_time", "awakening_type"]]
            data_split[day] = data_day

        data_concat = pd.concat(data_split, names=["date"])
        data_concat = data_concat.reset_index("timestamp")

        if add_day_id:
            data_concat = data_concat.assign(**{"day_id": range(1, len(data_concat) + 1)})
            data_concat = data_concat.set_index("day_id", append=True)
        return data_concat

    def export_times(
        self,
        include_sampling_times: Optional[bool] = True,
        include_evening_sample: Optional[bool] = True,
        include_awakening_times: Optional[bool] = True,
        add_day_id: Optional[bool] = True,
    ) -> pd.DataFrame:
        """Export sampling and/or awakening times from the participant's logs.

        Parameters
        ----------
        include_sampling_times : bool, optional
            ``True`` to include sampling times, ``False`` to exclude. Default: ``True``
        include_evening_sample : bool, optional
            ``True`` to include evening sampling times, ``False`` to only include morning sampling times.
            Default: ``True``
        include_awakening_times : bool, optional
            ``True`` to include awakening times, ``False`` to exclude. Default: ``True``
        add_day_id : bool, optional
            ``True`` to add an index level with the day id. Default: ``False``

        Returns
        -------
        :class:`~pandas.DataFrame`
            dataframe with sampling and/or awakening times

        """
        list_data = []
        if include_sampling_times:
            data = self.sampling_times(include_evening_sample=include_evening_sample, add_day_id=add_day_id)
            data = data[["sampling_time"]]
            data = data.droplevel("saliva_type")
            data = data.unstack(["saliva_id"])
            data.columns = ["_".join(map(str, col)) for col in data.columns]
            list_data.append(data)
        if include_awakening_times:
            data = self.awakening_times(add_day_id=add_day_id)
            data = data[["awakening_time", "awakening_type"]]
            list_data.append(data)

        return pd.concat(list_data, axis=1)
