"""Module containing example log data that can be processed."""

from pathlib import Path
from typing import Literal
from urllib.request import urlretrieve

from carwatch.logs import ParticipantLogs
from carwatch.utils._types import path_t

_EXAMPLE_DATA_PATH_LOCAL = Path(__file__).parent.parent.joinpath("example_data")
_EXAMPLE_DATA_PATH_HOME = Path.home().joinpath(".carwatch_data")
_REMOTE_DATA_PATH = "https://raw.githubusercontent.com/mad-lab-fau/carwatch/main/example_data/"


def _is_installed_manually() -> bool:
    """Check whether carwatch was installed manually and example data exists in the local path.

    Returns
    -------
    bool
        ``True`` if carwatch was installed manually, ``False`` otherwise

    """
    return (_EXAMPLE_DATA_PATH_LOCAL / "__init__.py").is_file()


def _get_data(file_name: str) -> path_t:  # pragma: no cover
    if _is_installed_manually():
        return _EXAMPLE_DATA_PATH_LOCAL.joinpath(file_name)
    path = _EXAMPLE_DATA_PATH_HOME.joinpath(file_name)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    return _fetch_from_remote(file_name, path)


def _fetch_from_remote(file_name: str, file_path: path_t) -> path_t:  # pragma: no cover
    """Download remote dataset (helper function).

    Parameters
    ----------
    file_name : str
        file name
    file_path : str
        path to file

    Returns
    -------
    :class:`~pathlib.Path`
        path to downloaded file

    """
    url = _REMOTE_DATA_PATH + file_name
    print(f"Downloading file {file_name} from remote URL: {url}.")
    urlretrieve(url, filename=file_path)
    return file_path


def get_carwatch_log_example(participant_id: Literal["AB12C", "DE34F", "GH56I"]) -> ParticipantLogs:  # pragma: no cover
    """Get example log file.

    Parameters
    ----------
    participant_id : int
        participant ID. Must be one of ``AB12C``, ``DE34F``, or ``GH56I``.

    Returns
    -------
    :class:`~carwatch.logs.ParticipantLogs`
        log data for the selected participant

    """
    file_name = f"zip_files/logs_{participant_id}.zip"
    return ParticipantLogs.from_zip_file(_get_data(file_name))
