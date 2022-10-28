import os
import subprocess
import sys
from pathlib import Path
from subprocess import check_call
from typing import Optional, Sequence, Union

import pandas as pd


class Study:
    """Class that represents a study."""

    MAX_NUM_SUBJECTS = 999  # maximal amount of subjects representable with EAN8

    def __init__(
        self,
        study_name: str,
        num_days: int,
        num_saliva_samples: int,
        num_subjects: Optional[int] = None,
        subject_path: Optional[Union[str, Path]] = None,
        subject_column: Optional[str] = "subject",
        subject_prefix: Optional[str] = None,
        has_evening_salivette: bool = False,
    ):
        """Class that represents a study.

        Parameters
        ----------
        study_name: str
            Study name that will be printed on the labels
        num_days: int
            Number of days the study will be conducted
        num_saliva_samples: int
            *Total* number of saliva samples per day (including a potential evening sample!)
        num_subjects: int, optional
            Number of subjects in the study
        subject_path: str or :class:`~pathlib.Path`, optional
            Path to a tabular list of all subjects
        subject_column: str, optional
            Only used when ``subject_path`` is set, specifies the column name containing the subejct ids,
            default value is ``"subject"``.
        subject_prefix: str, optional
            Add prefix to participant number (e.g., "VP_")
        has_evening_salivette: bool, optional
            Whether a saliva sample in the evening is also collected, default is ``False``

        """
        self.study_name = study_name
        self.num_days = num_days
        self.num_saliva_samples = num_saliva_samples
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
        if subject_prefix:
            subject_prefix = _sanitize_str_for_tex(subject_prefix)
        self.subject_prefix = subject_prefix
        self.has_evening_salivette = has_evening_salivette

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
            if _assert_file_ending(subject_path, [".csv", ".txt"]):
                subject_data = pd.read_csv(subject_path)
                subject_ids = subject_data[subject_column].apply(_sanitize_str_for_tex)
                return subject_ids.to_list()
            return None
        # _assert_file_ending throws value error if file has wrong ending/doesn't exist
        except ValueError as e:
            print(e)
            sys.exit(1)

    @property
    def subject_indices(self):
        return list(range(1, self.num_subjects + 1))

    @property
    def day_indices(self):
        return list(range(1, self.num_days + 1))

    @property
    def saliva_indices(self):
        return list(range(1, self.num_saliva_samples + 1))


def _assert_is_dir(path: Path) -> Optional[bool]:
    """Check if a path is a directory.

    Parameters
    ----------
    path : str
        path to check if it's a directory

    Returns
    -------
    ``True`` if ``path`` is a directory

    Raises
    ------
    ValueError
        if ``path`` is not a directory

    """
    # ensure pathlib
    file_name = Path(path)
    if not file_name.is_dir():
        raise ValueError(f"The path '{path}' is expected to be a directory, but it's not!")
    return True


def _write_to_file(file: Path, content: str):
    """Write a given text to a file.

    If `file` doesn't exist it is created, otherwise, it is truncated.

    Parameters
    ----------
    file: :class:`~pathlib.Path`
        path to file that will be written
    content : str
        string that will be inserted to file

    """
    # ensure pathlib
    file_name = Path(file)
    with open(file_name, "w+", encoding="utf-8") as fp:
        fp.write(content)


def _tex_to_pdf(output_dir: Path, tex_file: Union[str, Path]):
    """Run shell command to compile a tex file to a pdf document.

    Parameters
    ----------
    output_dir: path
        Path to directory where the output file will be stored
    tex_file: str or :class:`~pathlib.Path`
        Path to the `*.tex`-file that will be compiled

    Raises
    ------
    RuntimeError
        if ``pdflatex`` is not found

    """
    try:
        #  call pdflatex and suppress console output
        check_call(["pdflatex", f"-output-directory={output_dir}", tex_file], stdout=subprocess.DEVNULL, timeout=60)
    except FileNotFoundError as e:
        if os.name.startswith("win"):
            raise RuntimeError(
                "Apparently, you don't have Latex installed. "
                "Please install MikTex (from here: https://miktex.org/download), restart your computer, and try again."
            ) from e
        raise RuntimeError(
            "Apparently, you don't have Latex installed. "
            "Please install TexLive (from here: https://tug.org/texlive/) and try again."
        ) from e
    except subprocess.TimeoutExpired as e:
        # when pdflatex gets stuck, process will not end automatically
        raise RuntimeError(
            "Compilation aborted as it took too long. Please check your input parameters for plausibility."
        ) from e
    print(f"\nPDF created successfully and can be found here: {output_dir.absolute()}")


def _assert_file_ending(path: Path, ending: Union[str, Sequence[str]]) -> bool:
    """Check if a path points to an existing file with a certain file ending.

    Parameters
    ----------
    path : :class:`~pathlib.Path`
        path to check if it's a directory
    ending : str or list of str
        file ending or a list of file endings that the file is expected to have

    Returns
    -------
    ``True`` if ``path`` has the given file ending

    Raises
    ------
    ValueError
        if ``path`` is not pointing to a file, or
        if the file extension is invalid

    """
    if path.is_file():
        if isinstance(ending, str):
            ending = [ending]
        for end in ending:
            if str(path).endswith(end):
                return True
        raise ValueError("The file has an invalid extension! It needs to be either a .csv or .txt file!")
    raise ValueError(f"The path is '{path}' is not an existing file!")


def _sanitize_str_for_tex(string: str) -> str:
    r"""Escape special characters in a string to preserve them when compiled with pdflatex.

    The characters that are escaped are: `"&", "%", "$", "#", "_", "{", "}", "~", "^", "\"`.

    Parameters
    ----------
    string : str
       an arbitrary unescaped string

    Returns
    -------
    str
        Sanitized version of ``string`` with all characters of special meaning in latex escaped

    """
    escape_chars = ["&", "%", "$", "#", "_", "{", "}"]
    replace_chars = {"~": r"\textasciitilde", "^": r"\textasciicircum", r"\\": r"\textbackslash"}
    for c in escape_chars:
        string = string.replace(c, rf"\{c}")
    for c, val in replace_chars.items():
        string = string.replace(c, f"{val}")
    return string
