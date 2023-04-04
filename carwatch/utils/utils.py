"""Utility functions for the carwatch package."""
import os
import subprocess
import warnings
from pathlib import Path
from subprocess import check_call
from typing import Optional, Sequence, Union


def assert_is_dir(path: Path) -> Optional[bool]:
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


def write_to_file(file: Path, content: str):
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


def tex_to_pdf(output_dir: Path, tex_file: Union[str, Path]):
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


def assert_file_ending(path: Path, ending: Union[str, Sequence[str]]) -> bool:
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


def sanitize_str_for_tex(string: str) -> str:
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


def sanitize_str_for_qr(string: str, forbidden_chars: Sequence[str]) -> str:
    r"""Remove special characters in a string to prevent parsing problems when reading the data.

    Parameters
    ----------
    string : str
        an arbitrary unescaped string
    forbidden_chars : list
        characters that will be removed from the string

    Returns
    -------
    str
        Sanitized version of ``string`` with all forbidden characters removed

    """
    for c in forbidden_chars:
        if c in string:
            warnings.warn(f"Forbidden symbol `{c}` detected in input `{string}`, will be removed.")
        string = string.replace(c, "")
    return string
