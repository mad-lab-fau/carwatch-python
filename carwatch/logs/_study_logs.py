"""Log files from a complete study."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict, Literal, Optional, Sequence, Tuple

import pandas as pd

from carwatch.logs import ParticipantLogs
from carwatch.logs._utils import filter_folder_for_participant_logs
from carwatch.utils._types import path_t

if TYPE_CHECKING:  # pragma: no cover
    import matplotlib.pyplot as plt


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
    def participants(self) -> Sequence[str]:
        """Return the participants of the study."""
        return list(self._study_logs.keys())

    @classmethod
    def from_folder(
        cls,
        folder_path: path_t,
        extract_folder: Optional[bool] = False,
        overwrite_unzipped_logs: Optional[bool] = False,
        tz: Optional[str] = "Europe/Berlin",
        error_handling: Optional[Literal["ignore", "warn", "raise"]] = "raise",
    ) -> StudyLogs:
        """Create a :class:`~carwatch.logs.StudyLogs` object from a folder containing log files.

        Parameters
        ----------
        folder_path : path or str
            path to the folder containing the log files
        extract_folder : bool, optional
            ``True`` to extract the zip files to a folder, ``False`` to keep the zip files. Default: ``False``
        overwrite_unzipped_logs : bool, optional
            ``True`` to overwrite existing unzipped log files, ``False`` to keep the existing files. Default: ``False``
        tz : str, optional
            timezone of the log files. Default: "Europe/Berlin"
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
        file_list = filter_folder_for_participant_logs(folder_path)

        if len(file_list) == 0:
            raise FileNotFoundError(f"No log files found in folder {folder_path}.")

        for path in file_list:
            if path.is_file() and path.suffix == ".zip":
                logs = ParticipantLogs.from_zip_file(
                    path,
                    extract_folder=extract_folder,
                    overwrite_unzipped_logs=overwrite_unzipped_logs,
                    tz=tz,
                    error_handling=error_handling,
                )
            else:  # must be a folder
                logs = ParticipantLogs.from_folder(path, tz=tz, error_handling=error_handling)
            study_logs[logs.subject_id] = logs

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
        sampling_times: Optional[bool] = True,
        awakening_times: Optional[bool] = True,
        include_evening_sample: Optional[bool] = True,
        wide_format: Optional[bool] = False,
    ) -> pd.DataFrame:
        """Export the sampling and/or awakening times of all log files from the study as a :class:`~pandas.DataFrame`.

        Parameters
        ----------
        sampling_times : bool, optional
            ``True`` to include sampling times, ``False`` to exclude. Default: ``True``
        awakening_times : bool, optional
            ``True`` to include awakening times, ``False`` to exclude. Default: ``True``
        include_evening_sample : bool, optional
            ``True`` to include evening sampling times, ``False`` to only include morning sampling times.
            Default: ``True``
        wide_format : bool, optional
            ``True`` to return a wide format dataframe where one row represents one participant, ``False`` to return a
            dataframe where one row represents one day/night. Default: ``False``

        Returns
        -------
        :class:`~pandas.DataFrame`
            sampling and/or awakening times of all log files from the study as a :class:`~pandas.DataFrame`

        """
        data_dict = {
            key: participant_logs.export_times(
                sampling_times=sampling_times,
                awakening_times=awakening_times,
                include_evening_sample=include_evening_sample,
                wide_format=wide_format,
            )
            for key, participant_logs in self._study_logs.items()
        }
        if wide_format:
            return pd.concat(data_dict.values())

        return pd.concat(data_dict, names=["subject"])

    @property
    def android_versions(self) -> pd.DataFrame:
        """Return the Android versions of the different study participants as a :class:`~pandas.DataFrame`.

        Returns
        -------
        :class:`~pandas.DataFrame`
            Android versions of the different study participants as a :class:`~pandas.DataFrame`
        """
        return self._get_metadata("android_version")

    @property
    def app_versions(self):
        """Return the app versions of the different study participants as a :class:`~pandas.DataFrame`.

        Returns
        -------
        :class:`~pandas.DataFrame`
            App versions of the different study participants as a :class:`~pandas.DataFrame`
        """
        return self._get_metadata("app_version")

    @property
    def phone_models(self):
        """Return the phone models of the different study participants as a :class:`~pandas.DataFrame`.

        Returns
        -------
        :class:`~pandas.DataFrame`
            Phone models of the different study participants as a :class:`~pandas.DataFrame`
        """
        return self._get_metadata("phone_model")

    @property
    def phone_manufacturers(self):
        """Return the phone manufacturers of the different study participants as a :class:`~pandas.DataFrame`.

        Returns
        -------
        :class:`~pandas.DataFrame`
            Phone manufacturers of the different study participants as a :class:`~pandas.DataFrame`
        """
        return self._get_metadata("phone_manufacturer")

    def _get_metadata(self, metadata_type: str) -> pd.DataFrame:
        data = {key: getattr(logs, metadata_type) for key, logs in self._study_logs.items()}
        data = pd.Series(data).to_frame(name=metadata_type)
        data.index.name = "subject"
        return data

    def get_metadata_stats(self, metadata: str) -> pd.DataFrame:
        """Return the number of participants for each value of the given metadata.

        Parameters
        ----------
        metadata : str
            metadata to get the number of participants for each value of

        Returns
        -------
        :class:`~pandas.DataFrame`
            number of participants for each value of the given metadata

        """
        return pd.DataFrame(self._get_metadata(metadata).value_counts(), columns=["count"])

    def get_metadata_plot(self, metadata: str, **kwargs) -> Tuple[plt.Figure, plt.Axes]:  # pragma: no cover
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError as e:
            raise ImportError(
                "This function requires matplotlib and seaborn to be installed. "
                "Please install them either manually or by installing the 'carwatch' package "
                "using 'pip install carwatch[plotting]'."
            ) from e
        ax = kwargs.pop("ax", None)
        if ax is None:
            fig, ax = plt.subplots(figsize=kwargs.pop("figsize", None))
        else:
            fig = ax.get_figure()

        data = self.get_metadata_stats(metadata)

        palette = kwargs.pop("palette", sns.cubehelix_palette(len(data), start=0.5, rot=-0.75))
        ax = sns.barplot(data=data.reset_index(), x=metadata, y="count", ax=ax, palette=palette, **kwargs)

        if metadata in ["phone_model", "log_dates"]:
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

        return fig, ax
