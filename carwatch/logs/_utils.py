from typing import Sequence
from zipfile import ZipFile, ZipInfo

from carwatch.utils._types import path_t


def filter_folder_for_participant_logs(folder_path: path_t) -> Sequence[path_t]:
    """Filter a folder for participant log files.

    The log files for one participant can either be a single zip file or a folder containing the log files.

    Parameters
    ----------
    folder_path : path or str
        path to the folder containing the log files

    Returns
    -------
    list of path or str
        list of participant logs in the folder

    """
    file_list = [
        f
        for f in sorted(folder_path.glob("*"))
        if ((f.is_file() and f.suffix == ".zip") or f.is_dir())
        and not f.name.startswith(".")  # ignore hidden files
        and not f.name.startswith("__")  # ignore hidden files
    ]
    return file_list


def filter_zip_file_for_logs(zip_ref: ZipFile) -> Sequence[ZipInfo]:
    """Filter the log files from a zip file.

    Parameters
    ----------
    zip_ref : :class:`~zipfile.ZipFile`
        zip file to filter

    Returns
    -------
    list of :class:`~zipfile.ZipInfo`
        list of log files in the zip file

    """
    file_list = [
        f
        for f in zip_ref.filelist
        if f.filename.endswith(".csv")
        and not f.filename.startswith(".")  # ignore hidden files
        and not f.filename.startswith("__")  # ignore hidden files
    ]
    file_list.sort(key=lambda x: x.filename)
    return file_list
