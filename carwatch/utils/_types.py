"""Some custom helper types to make type hints and type checking easier."""

from pathlib import Path
from typing import Sequence, TypeVar, Union, Hashable

_Hashable = Union[Hashable, str]
path_t = TypeVar("path_t", str, Path)  # pylint:disable=invalid-name
str_t = TypeVar("str_t", str, Sequence[str])  # pylint:disable=invalid-name
