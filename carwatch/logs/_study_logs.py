"""Log files from a complete study."""
from pathlib import Path
from typing import Dict, Literal, Optional

import pandas as pd

from carwatch.logs import ParticipantLogs
from carwatch.utils._types import path_t


class StudyLogs:
    """Class representing log files from a complete study."""

    def __init__(self, study_logs: Dict[str, ParticipantLogs]):
        """Initialize the class.

        .. note::
            This class is not intended to be used directly. Use :meth:`~carwatch.logs.StudyLogs.from_folder`
            to create a :class:`~carwatch.logs.StudyLogs` object from a folder containing log files.

        Parameters
        ----------
        study_logs : dict of str and :class:`~carwatch.logs.ParticipantLogs`
            dictionary containing the log files for each participant

        """
        self._study_logs = study_logs

    def __getitem__(self, key):
        """Return the log file for the given key."""
        return self._study_logs[key]

    def __iter__(self):
        """Iterate over the log files."""
        return iter(self._study_logs)

    def __len__(self):
        """Return the number of log files."""
        return len(self._study_logs)

    @property
    def participants(self):
        """Return the participants of the study."""
        return list(self._study_logs.keys())

    @classmethod
    def from_folder(
        cls, folder_path: path_t, error_handling: Optional[Literal["ignore", "warn", "raise"]] = "ignore"
    ) -> "StudyLogs":
        """Create a :class:`~carwatch.logs.StudyLogs` object from a folder containing log files.

        Parameters
        ----------
        folder_path : path or str
            path to the folder containing the log files
        error_handling : {"ignore", "warn", "raise"}, optional
            how to handle error when parse log data. ``error_handling`` can be one of the following:

            * "ignore" to ignore warning.
            * "warn" to issue warning when no "Subject ID Set" action was found in the data (indicating that a
              participant did not correctly register itself for the study or that log data is corrupted)
            * "raise" to raise an exception when no "Subject ID Set" action was found in the data.
            Default: "ignore"

        Returns
        -------
        :class:`~carwatch.logs.StudyLogs`
            :class:`~carwatch.logs.StudyLogs` object containing the log files

        """
        folder_path = Path(folder_path)
        study_logs = {}
        for path in sorted(folder_path.glob("*")):
            if path.is_dir():
                logs = ParticipantLogs.from_folder(path, error_handling=error_handling)
            elif path.is_file() and path.suffix == ".zip":
                logs = ParticipantLogs.from_zip_file(path, error_handling=error_handling)
            else:
                continue
            study_logs[logs.subject_id] = logs

        if len(study_logs) == 0:
            raise ValueError(f"No log files found in folder {folder_path}.")
        return cls(study_logs)

    def data_as_df(self):
        """Return the log files as a :class:`~pandas.DataFrame`.

        Returns
        -------
        :class:`~pandas.DataFrame`
            log files as a :class:`~pandas.DataFrame`

        """
        return pd.concat(
            {key: participant_logs.data_as_df() for key, participant_logs in self._study_logs.items()},
            names=["subject"],
        )

    def export_times(
        self,
        include_sampling_times: Optional[bool] = True,
        include_evening_sample: Optional[bool] = True,
        include_awakening_times: Optional[bool] = True,
        add_day_id: Optional[bool] = True,
    ) -> pd.DataFrame:
        """Export the sampling and/or awakening times of all log files from the study as a :class:`~pandas.DataFrame`.

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
            ``True`` to add an index level with the night id. Default: ``False``

        Returns
        -------
        :class:`~pandas.DataFrame`
            sampling and/or awakening times of all log files from the study as a :class:`~pandas.DataFrame`

        """
        return pd.concat(
            {
                key: participant_logs.export_times(
                    include_sampling_times=include_sampling_times,
                    include_evening_sample=include_evening_sample,
                    include_awakening_times=include_awakening_times,
                    add_day_id=add_day_id,
                )
                for key, participant_logs in self._study_logs.items()
            },
            names=["subject"],
        )
