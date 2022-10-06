import os
import subprocess
import sys
from pathlib import Path
from subprocess import check_call
from typing import Optional, Union

import pandas as pd


class Study:
    """Class that represents a study."""

    def __init__(
        self,
        study_name: str,
        num_days: int,
        num_saliva_samples: int,
        num_subjects: Optional[int] = None,
        subject_path: Optional[Union[str, Path]] = None,
        subject_column: Optional[str] = "subject",
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
        has_evening_salivette: bool, optional
            Whether a saliva sample in the evening is also collected, default is ``False``
        """
        self.study_name = study_name
        self.num_days = num_days
        self.num_saliva_samples = num_saliva_samples
        if subject_path:
            self.subject_ids = self._determine_subject_ids(subject_path, subject_column)
            self.num_subjects = len(self.subject_ids)
        elif num_subjects:
            self.num_subjects = num_subjects
            self.subject_ids = [str(i) for i in range(1, self.num_subjects + 1)]
        else:
            raise ValueError(
                "Subject number unknown! Specification of either `num_subjects` or `subject_data` required!"
            )

        self.has_evening_salivette = has_evening_salivette

    def _determine_subject_ids(self, subject_path: Union[str, Path], subject_column: str):
        """
        Extract the IDs of the study participants depending on the content of the subject data file.
        It is assumed that the subject data contains comma-separated tabular data with a header row.

        Parameters
        ----------
        study_name: str or :class:`~pathlib.Path`
            Path to either a `*.csv` or `*.txt` file that contains the tabular participant data,
            assumes that every row corresponds to one subject
        subject_column: name of the column that contains the subject ids

        Returns
        -------
        The length of the subject list, i.e., the number of subjects
        """
        subject_path = Path(subject_path)
        try:
            if _assert_file_ending(subject_path, [".csv", ".txt"]):
                subject_data = pd.read_csv(subject_path)
                subject_ids = subject_data[subject_column].apply(_sanitize_str_for_tex)
                return subject_ids.to_list()
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
        raise ValueError("The path '{}' is expected to be a directory, but it's not!".format(path))
    return True


def _write_to_file(file: Path, content: str):
    """
    Writes a given text to a file.
    string `content` to `file`;
    if `file` doesn't exist create it, otherwise truncate it

    Parameters
    ----------
    file: :class:`~pathlib.Path`
        path to file that will be written
    content : str
        string that will be inserted to file
    """
    # ensure pathlib
    file_name = Path(file)
    with open(file_name, "w+") as fp:
        fp.write(content)


def _tex_to_pdf(output_dir: Path, tex_file: Union[str, Path]):
    """Run shell command to compile a tex file to a pdf document

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
    except FileNotFoundError:
        if os.name.startswith("win"):
            raise RuntimeError(
                "Apparently you don't have Latex installled. Please install MikTex (from here: https://miktex.org/download), restart your computer, and try again."
            )
        else:
            raise RuntimeError(
                "Apparently you don't have Latex installled. Please install TexLive (from here: https://tug.org/texlive/) and try again."
            )
    except subprocess.TimeoutExpired:
        # when pdflatex gets stuck, process will not end automatically
        raise RuntimeError(
            "Compilation aborted as it took too long. Please check your input parameters for plausibility."
        )
    print(f"\nPDF created succesfully and can be found here: {output_dir.absolute()}")


def _assert_file_ending(path: Path, ending: Union[str, list[str]]) -> bool:
    """
    Check if a path points to an existing file with a certain file ending.

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
    else:
        raise ValueError("The path is '{}' is not an existing file!".format(path))


def _sanitize_str_for_tex(string: str) -> str:
    """
    Escapes the characters `"&", "%", "$", "#", "_", "{", "}", "~", "^", "\"` in a String to preserve them when compiled with pdflatex

    Parameters
    ----------
    string : str
       an arbitrary unescaped string

    Returns
    -------
    Sanitized version of ``string`` with all characters of special meaning in latex escaped
    """
    escape_chars = ["&", "%", "$", "#", "_", "{", "}"]
    replace_chars = {"~": r"\textasciitilde", "^": r"\textasciicircum", r"\\": r"\textbackslash"}
    for c in escape_chars:
        string = string.replace(c, rf"\{c}")
    for c in replace_chars.keys():
        string = string.replace(c, f"{replace_chars[c]}")
    return string
