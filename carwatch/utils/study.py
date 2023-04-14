"""Module that contains the :class:`~carwatch.utils.study.Study` class."""
import sys
from pathlib import Path
from typing import Optional, Sequence, Union

import pandas as pd

from carwatch.utils.utils import assert_file_ending


class Study:
    """Class that represents a study."""

    MAX_NUM_SUBJECTS = 999  # maximal amount of subjects representable with EAN8

    def __init__(
        self,
        study_name: str,
        num_days: int,
        num_samples: int,
        num_subjects: Optional[int] = None,
        subject_path: Optional[Union[str, Path]] = None,
        subject_column: Optional[str] = "subject",
        subject_prefix: Optional[str] = None,
        has_evening_sample: bool = False,
        sample_prefix: Optional[str] = "S",
        start_sample_from_zero: bool = False,
    ):
        """Class that represents a study.

        Parameters
        ----------
        study_name: str
            Study name that will be printed on the labels
        num_days: int
            Number of days the study will be conducted
        num_samples: int
            *Total* number of biomarker samples per day (including a potential evening sample!)
        num_subjects: int, optional
            Number of subjects in the study
        subject_path: str or :class:`~pathlib.Path`, optional
            Path to a tabular list of all subjects
        subject_column: str, optional
            Only used when ``subject_path`` is set, specifies the column name containing the subject ids,
            default value is ``"subject"``.
        subject_prefix: str, optional
            Add prefix to participant number (e.g., "VP_")
        has_evening_sample: bool, optional
            Whether a biomarker sample in the evening is also collected, default is ``False``
        sample_prefix: str, optional
            Abbreviation of the type of sample taken, default is ``'S'`` for 'Saliva'
        start_sample_from_zero: bool, optional
            Whether the ID of the first biomarker sample is 0, default is ``False``
            When set to ``False``, ID starts from 1

        """
        self.study_name = study_name
        self.num_days = num_days
        self.num_samples = num_samples
        self.subject_path = subject_path
        if self.subject_path:
            self.subject_ids = self._determine_subject_ids(subject_path, subject_column)
            self.num_subjects = len(self.subject_ids)
        elif num_subjects:
            self.num_subjects = num_subjects
            self.subject_ids = [str(i) for i in range(1, self.num_subjects + 1)]
        else:
            raise ValueError(
                "Subject number unknown! Specification of either `num_subjects` or `subject_data` required!"
            )
        if self.num_subjects > Study.MAX_NUM_SUBJECTS:
            raise ValueError(f"Sorry, studies with more than {Study.MAX_NUM_SUBJECTS} participants are not supported!")
        # if subject_prefix:
        #     subject_prefix = subject_prefix
        self.subject_prefix = subject_prefix
        self.has_evening_sample = has_evening_sample
        self.start_sample_from_zero = start_sample_from_zero
        self.sample_prefix = sample_prefix

    @staticmethod
    def _determine_subject_ids(subject_path: Union[str, Path], subject_column: str) -> Optional[Sequence[str]]:
        """Extract the IDs of the study participants.

        The IDs uf the study participants are extracted depending on the content of the subject data file.
        It is assumed that the subject data contains comma-separated tabular data with a header row.

        Parameters
        ----------
        subject_path : str or :class:`~pathlib.Path`
            Path to either a `*.csv` or `*.txt` file that contains the tabular participant data,
            assumes that every row corresponds to one subject
        subject_column : str
            name of the column that contains the subject ids

        Returns
        -------
        list
            list with subject IDs

        """
        subject_path = Path(subject_path)
        try:
            if assert_file_ending(subject_path, [".csv", ".txt"]):
                subject_data = pd.read_csv(subject_path)
                subject_ids = subject_data[subject_column]
                return subject_ids.to_list()
            # _assert_file_ending throws value error if file has wrong ending/doesn't exist
        except ValueError as e:
            print(e)
            sys.exit(1)
        return None

    def get_subject_name(self, subject_index: int) -> str:
        """Return the name of a subject.

        Parameters
        ----------
        subject_index : int
            index of the subject

        Returns
        -------
        str
            name of the subject

        """
        if self.subject_path:
            # no prefix or padding used
            return self.subject_ids[subject_index]
        # use padding and prefix if specified
        subject_name_padding = len(str(self.num_subjects))  # length of zero-padding depending on subject count
        subject_name = f"{subject_index:0{subject_name_padding}d}"
        if self.subject_prefix:
            subject_name = f"{self.subject_prefix}{subject_name}"
        return subject_name

    @property
    def subject_indices(self):
        """Return a list of subject indices.

        Returns
        -------
        list
            list of subject indices

        """
        return list(range(1, self.num_subjects + 1))

    @property
    def subject_names(self):
        """Return a list of subject names.

        Returns
        -------
        list
            list of subject names

        """
        return [self.get_subject_name(index - 1) for index in self.subject_indices]

    @property
    def day_indices(self):
        """Return a list of day indices.

        Returns
        -------
        list
            list of day indices

        """
        return list(range(1, self.num_days + 1))

    @property
    def sample_indices(self):
        """Return a list of sample indices.

        Returns
        -------
        list
            list of sample indices

        """
        return list(range(0, self.num_samples))
