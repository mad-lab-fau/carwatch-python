from pathlib import Path
from subprocess import check_call
from typing import Optional


class Study:
    """Class that represents a study."""

    def __init__(
            self,
            study_name: str,
            num_subjects: int,
            num_days: int,
            num_saliva_samples: int,
            has_evening_salivette: bool = False,
    ):
        """Class that represents a study.

        Parameters
        ----------
        study_name: str
            Study name that will be printed on the labels
        num_subjects: int
            Number of subjects in the study
        num_days: int
            Number of days the study will be conducted
        num_saliva_samples: int
            *Total* number of saliva samples per day (including a potential evening sample!)
        has_evening_salivette: bool
            Whether a saliva sample in the evening is also collected
        """
        self.study_name = study_name
        self.num_subjects = num_subjects
        self.num_days = num_days
        self.num_saliva_samples = num_saliva_samples
        self.has_evening_salivette = has_evening_salivette

    @property
    def subject_ids(self):
        # TODO: read from file if provided
        return list(range(1, self.num_subjects + 1))

    @property
    def day_ids(self):
        return list(range(1, self.num_days + 1))

    @property
    def saliva_ids(self):
        # TODO has_evening_salivette is ignored
        return list(range(1, self.num_saliva_samples + 1))


def _assert_is_dir(path: Path, raise_exception: Optional[bool] = True) -> Optional[bool]:
    """Check if a path is a directory.

    Parameters
    ----------
    path : str
        path to check if it's a directory
    raise_exception : bool, optional
        whether to raise an exception or return a bool value

    Returns
    -------
    ``True`` if ``path`` is a directory, ``False`` otherwise (if ``raise_exception`` is ``False``)

    Raises
    ------
    ValueError
        if ``raise_exception`` is ``True`` and ``path`` is not a directory

    """
    # ensure pathlib
    file_name = Path(path)
    if not file_name.is_dir():
        if raise_exception:
            raise ValueError("The path '{}' is expected to be a directory, but it's not!".format(path))
        return False

    return True


def _write_to_file(file: Path, content: str):
    """
    Write the string `content` to `file`;
    if `file` doesn't exist create it, otherwisen truncate it
    """
    # ensure pathlib
    file_name = Path(file)
    with open(file_name, "w+") as fp:
        fp.write(content)


def _tex_to_pdf(output_dir: Path, output_file: str):
    # TODO: check if pdflatex is installed
    print(check_call(["pdflatex", f"-output-directory={output_dir}", output_file]))
