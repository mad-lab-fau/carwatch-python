"""Internal helpers for dataset validation."""
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

from carwatch.utils._types import _Hashable, path_t
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
            raise ValueError(f"The path '{path}' is expected to be a directory, but it's not!")
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
    :exc:`~carwatch.utils.exceptions.FileExtensionError`
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
    :exc:`~carwatch.utils.exceptions.ValidationError`
        if ``raise_exception`` is ``True`` and ``obj`` is none of the expected data types

    """
    if not isinstance(obj, dtype):
        if raise_exception:
            raise ValidationError(f"The data object is expected to be one of ({dtype},). But it is a {type(obj)}")
        return False
    return True


def _assert_has_columns(
    df: pd.DataFrame,
    columns_sets: Sequence[Union[List[_Hashable], List[str], pd.Index]],
    raise_exception: Optional[bool] = True,
) -> Optional[bool]:
    """Check if the dataframe has at least all columns sets.

    Parameters
    ----------
    df : :class:`~pandas.DataFrame`
        The dataframe to check
    columns_sets : list
        Column set or list of column sets to check
    raise_exception : bool, optional
        whether to raise an exception or return a bool value

    Returns
    -------
    ``True`` if ``df`` has the expected column names, ``False`` otherwise (if ``raise_exception`` is ``False``)

    Raises
    ------
    :exc:`~carwatch.utils.exceptions.ValidationError`
        if ``raise_exception`` is ``True`` and ``df`` does not have the expected index level names

    Examples
    --------
    >>> df = pd.DataFrame()
    >>> df.columns = ["col1", "col2"]
    >>> _assert_has_columns(df, [["other_col1", "other_col2"], ["col1", "col2"]])
    >>> # This raises no error, as df contains all columns of the second set

    """
    columns = df.columns
    result = False
    for col_set in columns_sets:
        result = result or all(v in columns for v in col_set)

    if result is False:
        if len(columns_sets) == 1:
            helper_str = f"the following columns: {columns_sets[0]}"
        else:
            helper_str = f"one of the following sets of columns: {columns_sets}"
        if raise_exception:
            raise ValidationError(
                "The dataframe is expected to have {}. Instead it has the following columns: {}".format(
                    helper_str, list(df.columns)
                )
            )
    return result


def _assert_has_index_levels(
    df: pd.DataFrame,
    index_levels: Iterable[_Hashable],
    match_atleast: Optional[bool] = False,
    match_order: Optional[bool] = False,
    raise_exception: Optional[bool] = True,
) -> Optional[bool]:
    """Check if the dataframe has all index level names.

    Parameters
    ----------
    df : :class:`~pandas.DataFrame`
        The dataframe to check
    index_levels : list
        Set of index level names to check
    match_atleast : bool, optional
        Whether the MultiIndex columns have to have at least the specified column levels (``True``)
        or exactly match the column levels (``False``)
    match_order : bool, optional
        Whether to also match the level order
    raise_exception : bool, optional
        whether to raise an exception or return a bool value

    Returns
    -------
    ``True`` if ``df`` has the expected index level names, ``False`` otherwise (if ``raise_exception`` is ``False``)

    Raises
    ------
    :exc:`~carwatch.utils.exceptions.ValidationError`
        if ``raise_exception`` is ``True`` and ``df`` does not have the expected index level names

    """
    return _multiindex_level_names_helper(
        df,
        level_names=index_levels,
        idx_or_col="index",
        match_atleast=match_atleast,
        match_order=match_order,
        raise_exception=raise_exception,
    )


def _multiindex_level_names_helper(
    df: pd.DataFrame,
    level_names: Iterable[_Hashable],
    idx_or_col: str,
    match_atleast: Optional[bool] = False,
    match_order: Optional[bool] = False,
    raise_exception: Optional[bool] = True,
) -> Optional[bool]:

    if isinstance(level_names, str):
        level_names = [level_names]

    ex_levels = list(level_names)
    ac_levels = list(df.index.names) if idx_or_col == "index" else list(df.columns.names)

    expected = _multiindex_level_names_helper_get_expected_levels(ac_levels, ex_levels, match_atleast, match_order)

    if not expected:
        if raise_exception:
            raise ValidationError(
                "The dataframe is expected to have exactly the following {} level names {}, "
                "but it has {}".format(idx_or_col, level_names, ac_levels)
            )
        return False
    return True


def _multiindex_check_helper(
    df: pd.DataFrame,
    idx_or_col: str,
    expected: Optional[bool] = True,
    nlevels: Optional[int] = 2,
    nlevels_atleast: Optional[int] = False,
    raise_exception: Optional[bool] = True,
) -> Optional[bool]:

    has_multiindex, nlevels_act = _multiindex_check_helper_get_levels(df, idx_or_col)

    if has_multiindex is not expected:
        return _multiindex_check_helper_not_expected(idx_or_col, nlevels, nlevels_act, expected, raise_exception)

    if has_multiindex is True:
        expected = nlevels_act >= nlevels if nlevels_atleast else nlevels_act == nlevels
        if not expected:
            if raise_exception:
                raise ValidationError(
                    "The dataframe is expected to have a MultiIndex with {0} {1} levels. "
                    "But it has a MultiIndex with {2} {1} levels.".format(nlevels, idx_or_col, nlevels_act)
                )
            return False
    return True


def _multiindex_check_helper_get_levels(df: pd.DataFrame, idx_or_col: str) -> Tuple[bool, int]:
    if idx_or_col == "index":
        has_multiindex = isinstance(df.index, pd.MultiIndex)
        nlevels_act = df.index.nlevels
    else:
        has_multiindex = isinstance(df.columns, pd.MultiIndex)
        nlevels_act = df.columns.nlevels

    return has_multiindex, nlevels_act


def _multiindex_check_helper_not_expected(
    idx_or_col: str, nlevels: int, nlevels_act: int, expected: bool, raise_exception: bool
) -> Optional[bool]:
    if not expected:
        if raise_exception:
            raise ValidationError(
                "The dataframe is expected to have a single level as {0}. "
                "But it has a MultiIndex with {1} {0} levels.".format(idx_or_col, nlevels_act)
            )
        return False
    if raise_exception:
        raise ValidationError(
            "The dataframe is expected to have a MultiIndex with {0} {1} levels. "
            "It has just a single normal {1} level.".format(nlevels, idx_or_col)
        )
    return False


def _multiindex_level_names_helper_get_expected_levels(
    ac_levels: Sequence[str],
    ex_levels: Sequence[str],
    match_atleast: Optional[bool] = False,
    match_order: Optional[bool] = False,
) -> bool:
    if match_order:
        if match_atleast:
            ac_levels_slice = ac_levels[: len(ex_levels)]
            expected = ex_levels == ac_levels_slice
        else:
            expected = ex_levels == ac_levels
    elif match_atleast:
        expected = all(level in ac_levels for level in ex_levels)
    else:
        expected = sorted(ex_levels) == sorted(ac_levels)

    return expected
