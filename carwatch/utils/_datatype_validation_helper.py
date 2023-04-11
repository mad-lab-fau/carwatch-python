"""Internal helpers for dataset validation."""
from pathlib import Path
from typing import Optional, Sequence, Union, Tuple

from carwatch.utils._types import path_t
from carwatch.utils.exceptions import FileExtensionError, ValidationError


def _assert_is_dir(path: path_t, raise_exception: Optional[bool] = True) -> Optional[bool]:
    """Check if a path is a directory.

    Parameters
    ----------
    path : path or str
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


def _assert_file_extension(
    file_name: path_t, expected_extension: Union[str, Sequence[str]], raise_exception: Optional[bool] = True
) -> Optional[bool]:
    """Check if a file has the correct file extension.

    Parameters
    ----------
    file_name : path or str
        file name to check for correct extension
    expected_extension : str or list of str
        file extension (or a list of file extensions) to check for
    raise_exception : bool, optional
        whether to raise an exception or return a bool value

    Returns
    -------
    ``True`` if ``file_name`` ends with one of the specified file extensions, ``False`` otherwise
    (if ``raise_exception`` is ``False``)

    Raises
    ------
    :exc:`~biopsykit.exceptions.FileExtensionError`
        if ``raise_exception`` is ``True`` and ``file_name`` does not end with any of the specified
        ``expected_extension``

    """
    # ensure pathlib
    file_name = Path(file_name)
    if isinstance(expected_extension, str):
        expected_extension = [expected_extension]
    if file_name.suffix not in expected_extension:
        if raise_exception:
            raise FileExtensionError(
                f"The file name extension is expected to be one of {expected_extension}. "
                f"Instead it has the following extension: {file_name}"
            )
        return False
    return True


def _assert_is_dtype(
    obj, dtype: Union[type, Tuple[type, ...]], raise_exception: Optional[bool] = True
) -> Optional[bool]:
    """Check if an object has a specific data type.

    Parameters
    ----------
    obj : any object
        object to check
    dtype : type or list of type
        data type of tuple of data types to check
    raise_exception : bool, optional
        whether to raise an exception or return a bool value

    Returns
    -------
    ``True`` if ``obj`` is one of the expected data types, ``False`` otherwise (if ``raise_exception`` is ``False``)

    Raises
    ------
    :exc:`~biopsykit.exceptions.ValidationError`
        if ``raise_exception`` is ``True`` and ``obj`` is none of the expected data types

    """
    if not isinstance(obj, dtype):
        if raise_exception:
            raise ValidationError(f"The data object is expected to be one of ({dtype},). But it is a {type(obj)}")
        return False
    return True
